import os
import yaml
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
        'deploy': []
    }

    def __init__(self, scope, id, github_config: dict, project_config: dict):
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

    def _source(self, **github_config):
        artifact = cp.Artifact()

        checkout = cpa.BitBucketSourceAction(
            connection_arn=github_config['connection'],
            action_name="Source-{}".format(github_config['branch']),
            output=artifact,
            owner=github_config['owner'],
            repo=github_config['repo'],
            branch=github_config['branch'],
            code_build_clone_output=True
        )

        self.artifacts['sources'].append(artifact)
        self.actions['sources'].append(checkout)
        self.pipe.add_stage(stage_name='Source@{}'.format(github_config['repo']), actions=[checkout])

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

    def deploy(self, **deploy_config):
        deploy = cpa.CloudFormationCreateUpdateStackAction(
            action_name='Deploy',
            admin_permissions=True,
            extra_inputs=self.artifacts['builds'],
            # template_path=self.artifacts['builds'][0].at_path("cdk.out/iam-idp.template.json"),
            **deploy_config
        )
        self.actions['deploy'].append(deploy)
        self.pipe.add_stage(
            stage_name="Deploy",
            actions=self.actions['deploy']
        )

    @staticmethod
    def env(environment_variables: dict):
        envs = dict()
        for env, value in environment_variables.items():
            envs[env] = cb.BuildEnvironmentVariable(value=value)
        return envs
    
    @staticmethod
    def load_buildspec(specfile):
        with open(specfile, encoding="utf8") as fp:
            bsfile = fp.read()
            bs = yaml.safe_load(bsfile)
            return cb.BuildSpec.from_object(value=bs)
