import os
from aws_cdk import (
    aws_lambda,
    core
)
from aviv_cdk import cdk_lambda

path = os.path.dirname(__file__)

app = core.App()

stuff = core.Stack(app, 'testing')  # env=core.Environment(account='605901617242', region='eu-west-1'))

lbd = cdk_lambda.CDKLambda(
    stuff, 'lbd',
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

app.synth()