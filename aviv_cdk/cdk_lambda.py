import os
from aws_cdk import (
    aws_ssm as ssm,
    aws_lambda,
    core
)

class CDKLambda(core.Construct):
    _layer = None
    _lambda = None
    _assets: dict = None

    def __init__(self,  scope: core.Construct, id: str, *, lambda_attrs: aws_lambda.FunctionProps=None, layer_attrs=None, remote_account_grant=False, use_layer=True, cfn_outputs=False):
        """Provides a CDK Construct for AWS Lambda and Layers

        Args:
            scope (core.Construct): [description]
            id (str): [description]
            lambda_attrs (aws_lambda.FunctionProps, optional): [description]. Defaults to None.
            layer_attrs (aws_lambda.LayerVersionProps, optional): [description]. Defaults to None.
            remote_account_grant (bool, optional): [description]. Defaults to False.
            use_layer (bool, optional): [description]. Defaults to True.
        """
        super().__init__(scope, id)

        if layer_attrs:
            self._layer = aws_lambda.LayerVersion(
                self, "layer",
                **layer_attrs
            )
            ssm_name = "/{}/layer".format(id.replace('-', '/'))
            ssm.StringParameter(self, 'Layer', string_value=self._layer.layer_version_arn, parameter_name=ssm_name)
            if remote_account_grant:
                self._layer.add_permission('remote-account-grant', account_id='*')

        if lambda_attrs:
            self._lambda = aws_lambda.Function(
                self, "lambda", **lambda_attrs
            )
            if self._layer and use_layer:
                self._lambda.add_layers(self._layer)
        if cfn_outputs:
            core.CfnOutput(self, 'LambdaArn', value=self._lambda.function_arn)
            if self._layer:
                core.CfnOutput(self, 'LayerArn', value=self._layer.from_layer_version_arn)


    @staticmethod
    def _code_inline(filepath):
        """Streamline file into a string for a simple AWS Lambda

        Args:
            filepath ([type]): [description]

        Returns:
            [type]: [description]
        """
        with open(filepath, encoding="utf8") as fp:
            code = fp.read()
        return code
