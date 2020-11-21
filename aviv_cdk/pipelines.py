import os
import logging
import typing
from aws_cdk import (
    aws_codebuild as cb,
    aws_codepipeline as cp,
    aws_codepipeline_actions as cpa,
    # aws_codecommit as cc,
    aws_codestarconnections as csc,
    aws_s3,
    aws_kms,
    aws_ec2,
    aws_iam,
    core
)

class GithubConnection(core.Construct):
    def __init__(self, scope, id, github_config) -> None:
        super().__init__(scope, id)
        self.connection = csc.CfnConnection(
            self, 'github-connection',
            connection_name='{}'.format(github_config['owner']),
            host_arn=github_config['connection_host'],
            provider_type='GitHub'
        )


class Pipeline(cp.Pipeline):
    bucket: aws_s3.IBucket
    key: aws_kms.IKey
    stages = ['source', 'build', 'deploy']
    artifacts = core.typing.Mapping(stages, core.typing.List(cp.Artifact))
    actions = core.typing.Mapping(stages, core.typing.List(cpa.Action))

    def __init__(self, scope, id: str,
        *,
        artifact_bucket: aws_s3.IBucket=None,
        cross_account_keys: bool=None,
        cross_region_replication_buckets: core.typing.Mapping[str, aws_s3.IBucket]=None,
        pipeline_name: str=None,
        restart_execution_on_update: bool=None,
        role: aws_iam.IRole=None,
        stages: core.typing.List[cp.StageProps]=None):
        super().__init__(
            scope, id,
            artifact_bucket=artifact_bucket,
            cross_account_keys=cross_account_keys,
            cross_region_replication_buckets=cross_region_replication_buckets,
            pipeline_name=pipeline_name,
            restart_execution_on_update=restart_execution_on_update,
            role=role,
            stages=stages)

    def project(self, id: str,
        build_spec_file: str='buildspec.yml',
        *,  # Optionnal / std PipelineProject args
        allow_all_outbound: bool=None,
        badge: bool=None,
        build_spec: cb.BuildSpec=None,
        cache: cb.Cache=None,
        description: str=None,
        encryption_key: aws_kms.IKey=None,
        environment: cb.BuildEnvironment=cb.LinuxBuildImage.STANDARD_4_0,
        environment_variables: core.typing.Mapping[str, cb.BuildEnvironmentVariable]=None,
        file_system_locations: core.typing.List[cb.IFileSystemLocation]=None,
        grant_report_group_permissions: bool=None,
        project_name: str=None,
        role: aws_iam.IRole=None,
        security_groups: core.typing.List[aws_ec2.ISecurityGroup]=None,
        subnet_selection: aws_ec2.SubnetSelection=None,
        timeout: core.Duration=None,
        vpc: aws_ec2.IVpc=None):

        if not build_spec and build_spec_file:
            build_spec = Pipelines.load_buildspec(build_spec_file)

        return cb.PipelineProject(
            self, "project",
            project_name="{}".format(self.node.id),
            allow_all_outbound=allow_all_outbound,
            badge=badge,
            build_spec=build_spec,
            cache=cache,
            description=description,
            encryption_key=encryption_key,
            environment=environment,
            environment_variables=environment_variables,
            file_system_locations=file_system_locations,
            grant_report_group_permissions=grant_report_group_permissions,
            project_name=project_name,
            role=role,
            security_groups=security_groups,
            subnet_selection=subnet_selection,
            timeout=timeout,
            vpc=vpc,
        )

    def github_source(self, owner: str, repo: str, branch: str='master', connection: str=None, oauth: str=None):
        """[summary]

        Args:
            owner (str): Github organization/user
            repo (str): git repository url name
            branch (str): git branch
            connection (str): AWS codebuild connection_arn
            oauth (str): Github oauth token
        """
        artifact = cp.Artifact(artifact_name=repo.replace('-', '_'))

        if not connection and not oauth:
            raise SystemError("No credentials for Github provided")

        action_name = "{}@{}".format(repo, branch)
        action = cpa.BitBucketSourceAction(
            connection_arn=connection,
            action_name=action_name,
            output=artifact,
            owner=owner,
            repo=repo,
            branch=branch,
            code_build_clone_output=True
        )
        self.artifacts[action_name] = artifact
        self.actions[action_name] = action
        return artifact, action


class Pipelines(core.Construct):
    bucket: aws_s3.IBucket
    key: aws_kms.IKey
    artifacts = core.typing.Mapping(['source', 'build', 'deploy'], core.typing.List(cp.Artifact))
    # artifacts = {
    #     'sources': [],
    #     'builds': [],
    #     'deploy': []
    # }
    actions = {
        'sources': [],
        'builds': [],
        'deploy': {}
    }

    def __init__(self, scope, id, github_config: dict=None, project_config: dict=None):
        super().__init__(scope, id)

        self.bucket = aws_s3.Bucket(self, 'bucket',
            removal_policy=core.RemovalPolicy.RETAIN,
            encryption=aws_s3.BucketEncryption.KMS_MANAGED,
            versioned=True
        )

        self.pipe = Pipeline(self, 'pipe', cross_account_keys=True, pipeline_name=id + '-pipe')
        self.pipe.project(**project_config)

        if github_config:
            self.source(**github_config)
            self._build(self.artifacts['sources'][0])

    # def source(self, owner: str, repo: str, branch: str='master', connection: str=None, oauth: str=None, stage_it=True):
    def source(self, github_config: dict, stage_it=True):
        """[summary]

        Args:
            owner (str): Github organization/user
            repo (str): git repository url name
            branch (str): git branch
            connection (str): AWS codebuild connection_arn
            oauth (str): Github oauth token
        """
        artifact, checkout = self.pipe.github_source(**github_config)
        # self.artifacts['sources'].append(artifact)
        # self.actions['sources'].append(checkout)
        if stage_it:
            self.pipe.add_stage(stage_name='Source', actions=[checkout])
        # self.pipe.add_stage(stage_name='Source@{}'.format(repo), actions=[checkout])

    def _build(self, input, extra_inputs=[]):
        artifact = cp.Artifact()
        build = cpa.CodeBuildAction(
            outputs=[artifact],
            type=cpa.CodeBuildActionType.BUILD,
            action_name="Build",
            input=input,
            extra_inputs=extra_inputs,
            project=self.project
        )
        self.artifacts['builds'].append(artifact)
        self.actions['builds'].append(build)

        self.pipe.add_stage(
            stage_name="Build",
            actions=self.actions['builds']
        )

    def deploy(self, stack_name: str, *, template_path: str=None, action_name: str=None, stage_it: bool=True, **deploy_config):
        """Deploy stage for AWS CodePipeline

        Args:
            stack_name (str): CDK/CFN stack name to deploy
            template_path (str, optional): the generated CFN template path. Defaults to: 'stack_name'.template.json
            action_name (str, optional): AWS Pipeline action name. Defaults to: deploy-'stack_name'
            stage_it (bool, optional): Automagically stage this in pipeline. Defaults to True.
        """
        if not template_path:
            template_path = self.artifacts['builds'][0].at_path(
                "{}.template.json".format(stack_name)
            )
        if not action_name:
            action_name = "Deploy-{}".format(stack_name)

        deploy = cpa.CloudFormationCreateUpdateStackAction(
            admin_permissions=True,
            extra_inputs=self.artifacts['builds'],
            template_path=template_path,
            action_name=action_name,
            stack_name=stack_name,
            **deploy_config
        )
        # Save deploy action
        self.actions['deploy'][action_name] = deploy
        # Stage it (execute deploy) in pipeline
        if stage_it:
            self.pipe.add_stage(
                stage_name=action_name,
                actions=[self.actions['deploy'][action_name]]
            )

    @staticmethod
    def env(environment_variables: dict):
        envs = dict()
        for env, value in environment_variables.items():
            envs[env] = cb.BuildEnvironmentVariable(value=value)
        return envs
    
    @staticmethod
    def load_buildspec(specfile):
        import yaml

        with open(specfile, encoding="utf8") as fp:
            bsfile = fp.read()
            bs = yaml.safe_load(bsfile)
            return cb.BuildSpec.from_object(value=bs)
