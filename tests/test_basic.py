import pytest
import aviv_cdk

from aws_cdk import core

app = core.App()
stack = core.Stack(app, 'stack')

class TestAvivCdk:
    def test_version(self):
        assert aviv_cdk.__version__

    def test_loadpipeline(self):
        import aviv_cdk.pipelines as ap
        p = ap.Pipeline(stack, 'ptest')

        assert isinstance(p, ap.Pipeline)
