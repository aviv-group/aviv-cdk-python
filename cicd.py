import os
from aws_cdk import (
    aws_ssm as ssm,
    core
)
from aviv_cdk import (
    pipelines
)

secret_path = os.environ.get('SECRET_PATH', 'aviv/gtt/ace/tokens')
ssm_path = os.environ.get('SSM_PATH', '/aviv/ace/github/connection/aviv-group')


app = core.App()

TAGS = {tag: app.node.try_get_context(tag) for tag in ['environment', 'organisation', 'team', 'scope', 'application']}

cicd = core.Stack(app, 'aviv-cdk-cicd', env=core.Environment(account='605901617242', region='eu-west-1'))
pipe = pipelines.Pipelines(
    cicd, 'aviv-cdk-cicd',
    github_config=dict(
        connection=ssm.StringParameter.value_from_lookup(cicd, parameter_name=ssm_path),
        owner='aviv-group',
        repo='aviv-cdk-python',
        branch='master'
    ),
    project_config=dict(
        environment_variables=pipelines.Pipelines.env(dict(
            PYPI=app.node.try_get_context('pypi'),
            PYPI_TOKEN=core.SecretValue.secrets_manager(secret_path, json_field='PYPI_TOKEN')
        ))
    )
)

# pipe.deploy(
#     stack_name='aviv-cdk-iam-idp',
#     template_path=pipe.artifacts['builds'][0].at_path("cdk.out/aviv-cdk-iam-idp.template.json")
# )

app.synth()
