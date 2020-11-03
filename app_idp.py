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

app.synth()
