import os
from aws_cdk import (
    aws_lambda,
    core
)
from aviv_cdk import (
    cdk_lambda,
    pipelines
)

path = os.path.dirname(__file__)

app = core.App()

lbd = core.Stack(app, 'iam-idp')  # env=core.Environment(account='605901617242', region='eu-west-1'))
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
        code=aws_lambda.AssetCode('build/artifacts-cfn_resources.zip')
        # code=aws_lambda.AssetCode('build/layers/cfn_resources/')
    )
)

pipe = core.Stack(app, 'cicd')  # env=core.Environment(account='605901617242', region='eu-west-1'))

pipelines.Pipelines(
    pipe, 'pipeline',
    github_config=dict(
        oauth_token=core.SecretValue.secrets_manager('aviv/gtt/ace/tokens', json_field='GITHUB_TOKEN'),
        owner='aviv-group',
        repo='aviv-cdk-python',
        branch='master'
    ),
    project_config=dict(
        environment_variables=dict(
            PYPI_TOKEN=core.SecretValue.secrets_manager('aviv/gtt/ace/tokens', json_field='PYPI_TOKEN')
        ),
        build_spec='buildspec.yml'
    )
)

app.synth()
