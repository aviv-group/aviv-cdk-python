import os
import logging
from aws_cdk import (
    aws_codepipeline as cp,
    aws_codepipeline_actions as cpa,
    pipelines as cdkpipeline,
    core
)


class Pipelines(core.Construct):
    def __init__(self):
        print('hleo')
