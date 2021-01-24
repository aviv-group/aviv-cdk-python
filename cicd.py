import os
from aws_cdk import (
    aws_codebuild as cb,
    aws_ssm as ssm,
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
        'aviv-group': ssm.StringParameter.value_from_lookup(cicd, parameter_name='/aviv/ace/github/connection/aviv-group')
    }
)
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
pipe.github_source(
    owner='aviv-group',
    repo='aviv-cdk-python',
    branch='master'
)
pipe.build('aviv-cdk', sources=['aviv-cdk-python@master'], project=project)
# pipe.deploy_stack('aviv-cdk-iam-idp')
pipe.stage_all()

# pipe.deploy(
#     stack_name='aviv-cdk-iam-idp',
#     template_path=pipe.artifacts['builds'][0].at_path("cdk.out/aviv-cdk-iam-idp.template.json")
# )

app.synth()
