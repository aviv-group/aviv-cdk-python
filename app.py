import os
from aws_cdk import (
    aws_lambda,
    core
)
from aviv_cdk import (
    cdk_lambda,
    pipelines
)

secret_path = os.environ.get('SECRET_PATH', 'aviv/gtt/ace/tokens')
GITHUB_CONNECTION = os.environ.get('GITHUB_CONNECTION', 'arn:aws:codestar-connections:eu-west-1:605901617242:connection/83d824fc-5048-4f3f-b569-8251c98daae3')


app = core.App()

lbd = core.Stack(app, 'iam-idp')
cdk_lambda.CDKLambda(
    lbd, 'customresource-lambda',
    lambda_attrs=dict(
            code=aws_lambda.InlineCode(cdk_lambda.CDKLambda._code_inline('lambdas/iam_idp/saml.py')),
            handler='index.handler',
            timeout=core.Duration.seconds(20),
            runtime=aws_lambda.Runtime.PYTHON_3_7
    ),
    layer_attrs=dict(
        description='cfn_resources layer for idp',
        code=aws_lambda.AssetCode('build/layers/cfn_resources/')
    )
)

pipe = core.Stack(app, 'aviv-cdk-cicd')
pipelines.Pipelines(
    pipe, 'pipeline',
    github_config=dict(
        # oauth_token=core.SecretValue.secrets_manager(secret_path, json_field='GITHUB_TOKEN'),
        connection=GITHUB_CONNECTION,
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

app.synth()
