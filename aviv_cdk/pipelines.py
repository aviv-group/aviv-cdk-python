import os
import logging
from aws_cdk import (
    aws_codebuild as cb,
    aws_codepipeline as cp,
    aws_codepipeline_actions as cpa,
    # aws_codecommit as cc,
    aws_codestarconnections as csc,
    aws_s3 as s3,
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


class Pipelines(core.Construct):
    artifacts = {
        'sources': [],
        'builds': [],
        'build_extras': [],
        'deploy': []
    }
    actions = {
        'sources': [],
        'builds': [],
        'build_extras': [],
        'deploy': {}
    }

    def __init__(self, scope, id, github_config: dict, project_config: dict=dict()):
        super().__init__(scope, id)
        self.bucket = s3.Bucket(self, 'bucket',
            removal_policy=core.RemovalPolicy.RETAIN,
            encryption=s3.BucketEncryption.KMS_MANAGED,
            versioned=True
        )
        self.pipe = cp.Pipeline(self, 'pipe', cross_account_keys=True, pipeline_name=id + '-pipe')

        self._source(**github_config)
        self._project(**project_config)
        self._build(self.artifacts['sources'][0], self.artifacts['build_extras'])
        # self._deploy()

    def _project(self, **project_config):
        if 'build_spec' not in project_config:
            project_config['build_spec'] = 'buildspec.yml'
        project_config['build_spec'] = Pipelines.load_buildspec(project_config['build_spec'])
        self.project = cb.PipelineProject(
            self, "project",
            project_name="{}".format(self.node.id),
            environment=cb.LinuxBuildImage.STANDARD_4_0,
            cache=cb.Cache.bucket(bucket=self.bucket, prefix='codebuild-cache'),
            **project_config
        )

    def _source(self, owner: str, repo: str, branch: str='master', connection: str=None, oauth: str=None):
        """[summary]

        Args:
            owner (str): Github organization/user
            repo (str): git repository url name
            branch (str): git branch
            connection (str): AWS codebuild connection_arn
            oauth (str): Github oauth token
        """
        artifact = cp.Artifact()

        if not connection and not oauth:
            raise SystemError("No credentials for Github provided")

        checkout = cpa.BitBucketSourceAction(
            connection_arn=connection,
            action_name="Source-{}".format(branch),
            output=artifact,
            owner=owner,
            repo=repo,
            branch=branch,
            code_build_clone_output=True
        )

        self.artifacts['sources'].append(artifact)
        self.actions['sources'].append(checkout)
        self.pipe.add_stage(stage_name='Source@{}'.format(repo), actions=[checkout])

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
            action_name = "deploy-{}".format(stack_name)

        deploy = cpa.CloudFormationCreateUpdateStackAction(
            admin_permissions=True,
            extra_inputs=self.artifacts['builds'],
            template_path=template_path,
            action_name=action_name,
            stack_name=stack_name,
            **deploy_config
        )
        # Save deploy action
        self.actions['deploy'][action_name] = [deploy]
        # Stage it (execute deploy) in pipeline
        if stage_it:
            self.pipe.add_stage(
                stage_name=action_name,
                actions=self.actions['deploy'][action_name]
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
