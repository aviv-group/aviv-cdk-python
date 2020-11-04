from aws_cdk import (
    aws_ssm as ssm,
    core
)
from aviv_cdk import (
    __version__
)
import aviv_cdk

app = core.App()

TAGS = {tag: app.node.try_get_context(tag) for tag in ['environment', 'organisation', 'team', 'scope', 'application']}

stack = core.Stack(app, 'stack', tags=TAGS)

acdkversion = ssm.StringParameter(
    stack, 'aviv-cdk-version',
    string_value=aviv_cdk.__version__,
    parameter_name='/aviv/cdk/python/version'
)


app.synth()
