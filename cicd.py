import os
from aws_cdk import (
    core
)
from aviv_cdk import (
    pipelines
)


app = core.App()
tags = {tag: app.node.try_get_context(tag) for tag in ['environment', 'organisation', 'team', 'scope', 'application']}

# Our CICD stack ;)
cicd = core.Stack(app, 'aviv-cdk-cicd', env=core.Environment(account='605901617242', region='eu-west-1'))

# Create a codepipeline
pipe = pipelines.Pipeline(
    cicd, 'aviv-cdk-cicd',
    connections={'aviv-group': 'aws:ssm:/aviv/ace/github/connection/aviv-group'}
)

# Source from github
pipe.source('https://github.com/aviv-group/aviv-cdk-python@master')

# Build our project
secret_path = os.environ.get('SECRET_PATH', 'aviv/gtt/ace/tokens')
pipe.build('aviv-cdk', sources=['aviv-cdk-python@master'], environment_variables=pipelines.buildenv(dict(
    PYPI=app.node.try_get_context('pypi'),
    PYPI_TOKEN=f"aws:sm:{secret_path}:PYPI_TOKEN"
)))

pipe.stage_all()

app.synth()
