import os
from aws_cdk import core
from aviv_cdk import (
    stepfunctions,
    cdk_lambda
)

app = core.App()

TAGS = {tag: app.node.try_get_context(tag) for tag in ['environment', 'organisation', 'team', 'scope', 'application']}

stack = core.Stack(
    app, 'stack', tags=TAGS
)
stack.sfn = stepfunctions.Stepfunctions(stack, 'step')


app.synth()
