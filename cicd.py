import os
from aws_cdk import (
    aws_codebuild as cb,
    aws_iam,
    aws_ssm,
    aws_s3,
    core
)
from aviv_cdk import (
    pipelines
)

secret_path = os.environ.get('SECRET_PATH', 'aviv/gtt/ace/tokens')

app = core.App()

tags = {tag: app.node.try_get_context(tag) for tag in ['environment', 'organisation', 'team', 'scope', 'application']}

cicd = core.Stack(app, 'aviv-cdk-cicd', env=core.Environment(account='605901617242', region='eu-west-1'))
pipe = pipelines.Pipeline(
    cicd, 'aviv-cdk-cicd',
    connections={
        'aviv-group': aws_ssm.StringParameter.value_from_lookup(cicd, parameter_name='/aviv/ace/github/connection/aviv-group')
    }
)

pipe.github_source(
    owner='aviv-group',
    repo='aviv-cdk-python',
    branch='master'
)

# Build our project
project = pipe.create_project(
    'project',
    # environment_variables=pipelines.load_env(dict(
    environment_variables=dict(
        PYPI=cb.BuildEnvironmentVariable(value=app.node.try_get_context('pypi')),
        # PYPI_TOKEN=core.SecretValue.secrets_manager(secret_path, json_field='PYPI_TOKEN'),
        PYPI_TOKEN=cb.BuildEnvironmentVariable(
            value=f"{secret_path}:PYPI_TOKEN",
            type=cb.BuildEnvironmentVariableType.SECRETS_MANAGER
        )
    )
)
project.role.add_managed_policy(
    aws_iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name='SecretsManagerReadWrite')
)
pipe.build('aviv-cdk', sources=['aviv-cdk-python@master'], project=project)

pipe.stage_all()

app.synth()
