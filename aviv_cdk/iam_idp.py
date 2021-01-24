import os
import sys
import logging
from aws_cdk import (
    aws_iam as iam,
    aws_lambda,
    aws_ssm as ssm,
    aws_cloudformation as cfn,
    core
)
from .cdk_lambda import CDKLambda


class IAMIdpSAML(CDKLambda):
    _idp: cfn.CfnCustomResource = None

    def __init__(self,  scope: core.Construct, id: str, idp_name: str, idp_url: str, *, cfn_lambda:str = None, cfn_resources_path: str=None, debug=False):
        """Create an IAM SAML Identity Provider

        Args:
            scope (core.Construct): [description]
            id (str): [description]
            idp_name (str): IAM Idp name
            idp_url (str): Your SAML Identity provider URL
        """
        if not cfn_lambda:
            share_path = sys.prefix + '/share/aviv-cdk/' # TODO: FIX This should be cfn_resources?
            cfn_lambda = f"{share_path}iam-idp/saml.py"
        lambda_attrs=dict(
                code=aws_lambda.Code.from_inline(CDKLambda._code_inline(cfn_lambda)),
                handler='index.handler',
                timeout=core.Duration.seconds(20),
                runtime=aws_lambda.Runtime.PYTHON_3_7
        )
        if not cfn_resources_path:
            # TODO: check how to facilitate this? at least it is now documented in the README
            if not os.path.exists('build/artifacts-cfn_resources.zip'):
                raise FileNotFoundError('You need to generate a "build/artifacts-cfn_resources.zip" first or provide the path for the AssetCode in the cfn_resources_path argument')
            cfn_resources_path='build/artifacts-cfn_resources.zip'
        # layer_attrs=dict(
        layer_attrs=aws_lambda.LayerVersionProps(
            description='cfn_resources layer for idp',
            code=aws_lambda.Code.from_asset(cfn_resources_path),
            compatible_runtimes=[
                # aws_lambda.Runtime.PYTHON_3_6,
                aws_lambda.Runtime.PYTHON_3_7,
                aws_lambda.Runtime.PYTHON_3_8
            ]
        )

        # Create lambda function + layer
        super().__init__(scope, id, lambda_attrs=lambda_attrs, layer_attrs=layer_attrs._values, remote_account_grant=False)
        # Add required policies for the lambda to create an IAM idp
        self._lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=['iam:CreateSAMLProvider', 'iam:UpdateSAMLProvider', 'iam:DeleteSAMLProvider'],
                effect=iam.Effect.ALLOW,
                resources=['*']
            )
        )
        self._idp = cfn.CustomResource(
            self, "identityProvider",
            resource_type='Custom::SAMLProvider',
            provider=cfn.CustomResourceProvider.from_lambda(self._lambda.current_version),
            properties=dict(
                Name=idp_name,
                URL=idp_url
            )
        )
        self.response = self._idp.get_att("Response").to_string()

        # Export
        ssm_name = '/' + id.replace('-', '/')
        ssm.StringParameter(self, 'ssm', string_value=self._idp.ref, parameter_name=ssm_name)
        core.CfnOutput(self, 'SSMIAMIdpSAMLArn', value=ssm_name)
        core.CfnOutput(self, 'IAMIdpSAMLArn', value=self._idp.ref)

    @property
    def arn(self):
        return self._idp.ref

    @property
    def idp(self):
        return self._idp
