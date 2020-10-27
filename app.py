import os
from aws_cdk import (
    aws_ssm as ssm,
    aws_lambda,
    core
)
from aviv_cdk import (
    cdk_lambda,
    pipelines
)

secret_path = os.environ.get('SECRET_PATH', 'aviv/gtt/ace/tokens')
ssm_path = os.environ.get('SSM_PATH', '/aviv/ace/github/connection/aviv-group')


app = core.App()

lbd = core.Stack(app, 'aviv-cdk-iam-idp')
cdk_lambda.CDKLambda(
    lbd, 'aviv-cdk-iam-idp-lambda',
    lambda_attrs=dict(
            code=aws_lambda.InlineCode(cdk_lambda.CDKLambda._code_inline('lambdas/iam_idp/saml.py')),
            handler='index.handler',
            timeout=core.Duration.seconds(20),
            runtime=aws_lambda.Runtime.PYTHON_3_7
    ),
    layer_attrs=dict(
        description='cfn_resources layer for idp',
        code=aws_lambda.AssetCode('build/artifacts-cfn_resources.zip')
    )
)

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
        environment_variables=dict(
            PYPI_TOKEN=core.SecretValue.secrets_manager(secret_path, json_field='PYPI_TOKEN')
        ),
        build_spec='buildspec.yml'
    )
)
pipe.deploy(
    stack_name='aviv-cdk-iam-idp',
    template_path=pipe.artifacts['builds'][0].at_path("cdk.out/aviv-cdk-iam-idp.template.json")
)

app.synth()
