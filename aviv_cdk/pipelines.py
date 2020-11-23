import os
import logging
import typing
import constructs
from aws_cdk import (
    aws_codebuild as cb,
    aws_codepipeline as cp,
    aws_codepipeline_actions as cpa,
    aws_codestarconnections as csc,
    aws_cloudformation as cfn,
    aws_s3,
    aws_kms,
    aws_ec2,
    aws_iam,
    core
)


def load_env(environment_variables: dict):
    envs = dict()
    for env, value in environment_variables.items():
        envs[env] = cb.BuildEnvironmentVariable(value=value)
    return envs

def load_buildspec(specfile):
    import yaml

    with open(specfile, encoding="utf8") as fp:
        bsfile = fp.read()
        bs = yaml.safe_load(bsfile)
        return cb.BuildSpec.from_object(value=bs)


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
    project: cb.PipelineProject
    named_stages = ['source', 'build', 'deploy']
    connection: typing.Dict[str, str]
    artifacts: typing.Dict[str, typing.Dict[str, typing.Union[cp.Artifact, typing.List[cp.Artifact]]]]
    actions: typing.Dict[str, typing.Dict[str, cpa.Action]]
    pipe_role: aws_iam.IRole = None

    def __init__(
        self, scope, id: str,
        project_params: cb.PipelineProjectProps,
        *,
        connection: typing.Dict[str, str]=None,
        artifact_bucket: aws_s3.IBucket=None,
        cross_account_keys: bool=None,
        cross_region_replication_buckets: typing.Dict[str, aws_s3.IBucket]=None,
        pipeline_name: str=None,
        restart_execution_on_update: bool=None,
        role: aws_iam.IRole=None,
        pipe_role: aws_iam.IRole=None,
        stages: typing.List[cp.StageProps]=None) -> None:

        self.connection = connection
        self.artifacts = dict((sname, dict()) for sname in self.named_stages)
        self.actions = dict((sname, dict()) for sname in self.named_stages)

        logging.warning("Init pipeline: {}".format(pipeline_name))

        if not pipeline_name:
            pipeline_name = '{}-pipe'.format(id)

        if pipe_role:
            self.pipe_role = Pipeline._role(scope)
            # Override role
            role = self.pipe_role

        super().__init__(
            scope, id,
            artifact_bucket=artifact_bucket,
            cross_account_keys=cross_account_keys,
            cross_region_replication_buckets=cross_region_replication_buckets,
            pipeline_name=pipeline_name,
            restart_execution_on_update=restart_execution_on_update,
            role=role,
            stages=stages)

        #
        self.bucket = aws_s3.Bucket(
            self, 'bucket',
            bucket_name='{}-artifacts'.format(id),
            removal_policy=core.RemovalPolicy.RETAIN,
            encryption=aws_s3.BucketEncryption.KMS_MANAGED,
            versioned=True
        )

        self.project = self.create_project('default', **project_params._values)

    @staticmethod
    def _role(scope: constructs.Construct):
        """Mimic CDK role for multi-accounts deployment
        Just put everything in one Role...

        Args:
            scope ([type]): Aviv CDK pipeline stack

        Returns:
            IAM Role: [description]
        """
        return aws_iam.Role(
            scope, 'pipeRole',
            assumed_by=aws_iam.CompositePrincipal(
                aws_iam.ServicePrincipal('codebuild.amazonaws.com'),
                aws_iam.ServicePrincipal('codepipeline.amazonaws.com'),
                # aws_iam.ServicePrincipal('codedeploy.amazonaws.com'),
                aws_iam.AccountPrincipal(scope.account)
            ),
            inline_policies={
                'fullpower': aws_iam.PolicyDocument(statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            'codebuild:CreateReportGroup',
                            'codebuild:CreateReport',
                            'codebuild:UpdateReport',
                            'codebuild:BatchPutTestCases',
                            'codebuild:BatchPutCodeCoverages',
                            # 'codebuild:BatchGetBuilds',
                            # 'codebuild:StartBuild',
                            # 'codebuild:StopBuild',
                            # From there on, should be restricted to this proj
                            'codebuild:BatchGetBuilds',
                            'codebuild:StartBuild',
                            'codebuild:StopBuild',
                            'logs:CreateLogGroup',
                            'logs:CreateLogStream',
                            'logs:PutLogEvents'
                        ],
                        resources=['*'],
                        effect=aws_iam.Effect.ALLOW
                    )
                ])
            }
        )

    def create_project(self, id: str,
        *,  # Optionnal
        build_spec_file: str='buildspec.yml',
        # Std PipelineProject args
        allow_all_outbound: bool=None,
        badge: bool=None,
        build_spec: cb.BuildSpec=None,
        cache: cb.Cache=None,
        description: str=None,
        encryption_key: aws_kms.IKey=None,
        environment: cb.BuildEnvironment=cb.LinuxBuildImage.STANDARD_4_0,
        environment_variables: typing.Dict[str, cb.BuildEnvironmentVariable]=None,
        file_system_locations: typing.List[cb.IFileSystemLocation]=None,
        grant_report_group_permissions: bool=None,
        project_name: str=None,
        role: aws_iam.IRole=None,
        security_groups: typing.List[aws_ec2.ISecurityGroup]=None,
        subnet_selection: aws_ec2.SubnetSelection=None,
        timeout: core.Duration=None,
        vpc: aws_ec2.IVpc=None) -> cb.PipelineProject:


        if not build_spec and build_spec_file:
            build_spec = load_buildspec(build_spec_file)

        if not project_name:
            project_name = "{}".format(self.node.id)

        if not role and self.pipe_role:
            role = self.pipe_role

        logging.warning("Create project: {}".format(project_name))

        return cb.PipelineProject(
            self, "project",
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

    def stage_all(self):
        for sname in self.named_stages:
            actions = list(self.actions[sname].values())
            if actions:
                logging.warning("Stage: {} ({} actions)".format(sname, len(actions)))
                self.add_stage(stage_name=sname.capitalize(), actions=actions)
            else:
                logging.warning("Stage: No actions for: {}".format(sname))

    def source(self, url: str):
        if url.startswith('https://github.com/'):
            logging.warning("Source: {}".format(url))
            url = url.replace('https://github.com/', '').replace('.git', '')
            purl = url.split('/')
            self.github_source(owner=purl[0], repo=purl[1])

    def github_source(self, owner: str, repo: str, branch: str='master', connection_arn: str=None, oauth: str=None, role: aws_iam.IRole=None) -> typing.Dict[cpa.Action, cp.Artifact]:
        """[summary]

        Args:
            owner (str): Github organization/user
            repo (str): git repository url name
            branch (str): git branch
            connection_arn (str): AWS codebuild connection_arn
            oauth (str): Github oauth token
        """
        artifact = cp.Artifact(artifact_name=repo.replace('-', '_'))

        if not connection_arn and not oauth:
            if owner in self.connection:
                connection_arn = self.connection[owner]
            else:
                raise SystemError("No credentials for Github (need either a connnection_arn or oauth)")

        if not role and self.pipe_role:
            role = self.pipe_role

        action_name = "{}@{}".format(repo, branch)
        action = cpa.BitBucketSourceAction(
            connection_arn=connection_arn,
            action_name=action_name,
            output=artifact,
            owner=owner,
            repo=repo,
            role=role,
            branch=branch,
            code_build_clone_output=True
        )
        self.artifacts['source'][action_name] = artifact
        self.actions['source'][action_name] = action
        return action, artifact

    def build(
        self,
        action_name: str,
        *,
        sources: typing.List=None,
        input: cp.Artifact=None,
        project: cb.IProject=None,
        environment_variables: typing.Dict[str, cb.BuildEnvironmentVariable]=None,
        extra_inputs: typing.List[cp.Artifact]=None,
        outputs: typing.List[cp.Artifact]=[cp.Artifact()],
        type: cpa.CodeBuildActionType=cpa.CodeBuildActionType.BUILD,
        role: aws_iam.IRole=None,
        run_order: typing.Union[int, float]=None,
        variables_namespace: str=None) -> typing.Dict[cpa.Action, typing.List[cp.Artifact]]:

        if not project:
            project = self.project

        if not role and self.pipe_role:
            role = self.pipe_role

        if sources:
            logging.warning("Build soures: {}".format(sources))
            input=self.artifacts['source'][sources[0]]
            if len(sources) > 1:
                extra_inputs=[self.artifacts['source'][extra] for extra in sources[1:]]
        # artifacts = list(self.artifacts['source'].values())

        # # Try to use the first artifact from 'source' actions
        # if not input and artifacts:
        #     input = artifacts[0]
        #     # If no extra provided, pass additional artifacts that were eventually 'source'd
        #     if len(artifacts) > 1 and not extra_inputs:
        #         extra_inputs = artifacts[1:]
        # else:
        if not input:
            raise SyntaxError('No input artifact to build')

        logging.warning("Build: {} ({} extra(s))".format(action_name, len(extra_inputs)))
        action = cpa.CodeBuildAction(
            input=input,
            project=project,
            environment_variables=environment_variables,
            extra_inputs=extra_inputs,
            outputs=outputs,
            type=type,
            role=role,
            action_name=action_name,
            run_order=run_order,
            variables_namespace=variables_namespace
        )
        self.artifacts['build'][action_name] = outputs
        self.actions['build'][action_name] = action
        return action, outputs

    def deploy_stack(
        self,
        stack_name: str,
        *,
        action_name: str = None,
        admin_permissions: bool = True,
        template_path: cp.ArtifactPath = None,
        account: str = None,
        capabilities: typing.List[cfn.CloudFormationCapabilities] = None,
        deployment_role: aws_iam.IRole = None,
        extra_inputs: typing.List[cp.Artifact] = None,
        output: cp.Artifact = None,
        output_file_name: str = None,
        parameter_overrides: typing.Dict[str, typing.Any] = None,
        region: str = None,
        replace_on_failure: bool = None,
        template_configuration: cp.ArtifactPath = None,
        role: aws_iam.IRole = None,
        run_order: typing.Union[int, float] = None,
        variables_namespace: str = None):

        if not action_name:
            action_name = "Deploy-{}".format(stack_name)

        if not role and self.pipe_role:
            role = self.pipe_role

        logging.warning("Deploy CFN Stack: {}".format(stack_name))

        # If no template_path provided, pick the template using from the 1st built object
        if not template_path:
            artifacts = list(self.artifacts['build'].values())
            logging.warning(" -> Got artifacts from: {}".format(list(self.artifacts['build'].keys())))
            template_path = artifacts[0][0].at_path(
                "{}.template.json".format(stack_name)
            )

        action = cpa.CloudFormationCreateUpdateStackAction(
            admin_permissions=admin_permissions,
            stack_name=stack_name,
            template_path=template_path,
            account=account,
            capabilities=capabilities,
            deployment_role=deployment_role,
            extra_inputs=extra_inputs,
            output=output,
            output_file_name=output_file_name,
            parameter_overrides=parameter_overrides,
            region=region,
            replace_on_failure=replace_on_failure,
            template_configuration=template_configuration,
            role=role,
            action_name=action_name,
            run_order=run_order,
            variables_namespace=variables_namespace
        )
        self.artifacts['deploy'][action_name] = output
        self.actions['deploy'][action_name] = action


# class Pipelines(core.Construct):

#     def __init__(self, scope, id, github_config: dict=None, project_config: dict=None):
#         super().__init__(scope, id)

#         self.pipe = Pipeline(self, 'pipe', cross_account_keys=True, pipeline_name=id + '-pipe')
#         self.pipe.project(**project_config)

#         if github_config:
#             self.source(**github_config)
#             self._build(self.artifacts['sources'][0])

#     def source(self, github_config: dict, stage_it=True):
#         artifact, checkout = self.pipe.github_source(**github_config)
#         if stage_it:
#             self.pipe.add_stage(stage_name='Source', actions=[checkout])
#         # self.pipe.add_stage(stage_name='Source@{}'.format(repo), actions=[checkout])

#     def _build(self, input, extra_inputs=[]):

#         self.pipe.add_stage(
#             stage_name="Build",
#             actions=self.actions['builds']
#         )

#     def deploy(self, stack_name: str, *, template_path: str=None, action_name: str=None, stage_it: bool=True, **deploy_config):

#         action = None

#         # Save deploy action
#         self.actions['deploy'][action_name] = action
#         # Stage it (execute deploy) in pipeline
#         if stage_it:
#             self.pipe.add_stage(
#                 stage_name=action_name,
#                 actions=[self.actions['deploy'][action_name]]
#             )
