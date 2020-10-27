from aws_cdk import (
    aws_iam as iam,
    aws_secretsmanager as asm,
    core
)


class SecurityCredentials(core.Construct):
    user: iam.IUser

    def __init__(self, scope: core.Construct, id: str, *, user: iam.IUser=None) -> None:
        super().__init__(scope, id)
        self.user = user

    def console_password(self, secret_name: str, template: str = None, key: str = None):
        self.secret = asm.Secret(
            self,
            id,
            generate_secret_string=asm.SecretStringGenerator(
                secret_string_template=template,
                generate_string_key=key,
                password_length=24,
                exclude_characters='"@/\$'
            ),
            secret_name='{}{}'.format(secret_name, id)
        )
        return core.SecretValue(self.secret.secret_value.to_string())

    def access_key(self, user_name: str=None):
        if not user_name and self.user:
            user_name = self.user.user_name
        userkey = iam.CfnAccessKey(self, 'key', user_name=user_name)

        secret = asm.CfnSecret(
            self, 'userKey',
            name='iam/user/{}/accesskey'.format(user_name),
            secret_string='{{"AccessKeyId": "{}", "SecretAccessKey": "{}"}}'.format(
                userkey.ref,
                userkey.attr_secret_access_key
            )
        )
        return userkey.attr_secret_access_key

class Role(iam.Role):
    def __init__(self, scope: core.Construct, id: str, assumed_by=None, *, description=None, policies: list=None, external_ids=None, inline_policies=None,
        managed_policies=None, max_session_duration=None, path=None, permissions_boundary=None) -> None:
        """Same as a regular CDK AWS IAM Role except the Role name is defined by the CDK object 'id'.

        Args:
            scope (Construct): CDK Contruct/Stack
            id (str): Role id
            assumed_by: The IAM principal which can assume this role. You can later modify the assume role policy document by accessing it via the ``assumeRolePolicy`` property.
            description: A description of the role. It can be up to 1000 characters long. Default: - No description.
            policies: A list of AWS pre-defined IAM policies (lookup in arn:aws:iam::aws:policy/)
            external_ids: List of IDs that the role assumer needs to provide one of when assuming this role. If the configured and provided external IDs do not match, the AssumeRole operation will fail. Default: No external ID required
            inline_policies: A list of named policies to inline into this role. These policies will be created with the role, whereas those added by ``addToPolicy`` are added using a separate CloudFormation resource (allowing a way around circular dependencies that could otherwise be introduced). Default: - No policy is inlined in the Role resource.
            managed_policies: A list of managed policies associated with this role. You can add managed policies later using ``addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName(policyName))``. Default: - No managed policies.
            max_session_duration: The maximum session duration that you want to set for the specified role. This setting can have a value from 1 hour (3600sec) to 12 (43200sec) hours. Anyone who assumes the role from the AWS CLI or API can use the DurationSeconds API parameter or the duration-seconds CLI parameter to request a longer session. The MaxSessionDuration setting determines the maximum duration that can be requested using the DurationSeconds parameter. If users don't specify a value for the DurationSeconds parameter, their security credentials are valid for one hour by default. This applies when you use the AssumeRole* API operations or the assume-role* CLI operations but does not apply when you use those operations to create a console URL. Default: Duration.hours(1)
            path: The path associated with this role. For information about IAM paths, see Friendly Names and Paths in IAM User Guide. Default: /
            permissions_boundary: AWS supports permissions boundaries for IAM entities (users or roles). A permissions boundary is an advanced feature for using a managed policy to set the maximum permissions that an identity-based policy can grant to an IAM entity. An entity's permissions boundary allows it to perform only the actions that are allowed by both its identity-based policies and its permissions boundaries. Default: - No permissions boundary.
        """
        if policies:
            # Here the scope is the higher level construct/node, NOT self as the lookup is made before *this* construct calls its parent
            mpolicies = [
                iam.ManagedPolicy.from_managed_policy_arn(
                    # scope, '{}-{}-{}'.format(mpname, id, scope.node.id),
                    scope, '{}-{}'.format(mpname, id),
                    managed_policy_arn='arn:aws:iam::aws:policy/{}'.format(mpname)
                ) for mpname in policies
            ]
            if not managed_policies:
                managed_policies = list()
            managed_policies += mpolicies
        super().__init__(
            scope=scope, id=id, assumed_by=assumed_by, description=description, external_ids=external_ids, inline_policies=inline_policies,
            managed_policies=managed_policies, max_session_duration=max_session_duration, path=path, permissions_boundary=permissions_boundary, role_name=id
        )


class SAMLRole(Role):
    def __init__(self, scope: core.Construct, id: str, federated: str, *, description=None, external_ids=None, inline_policies=None,
        managed_policies=None, max_session_duration=None, path=None, permissions_boundary=None) -> None:
        """Same as CDK IAM Role above. The assumed_by is a FederatedPrincipal 'federated' (your IAM Idp arn).

        Args:
            federated: ARN of the AWS IAM Idp through which users assume this IAM Role
        """
        assumed_by=iam.FederatedPrincipal(
            federated=federated,
            conditions={
                'StringEquals': {'SAML:aud': 'https://signin.aws.amazon.com/saml'}
            },
            assume_role_action='sts:AssumeRoleWithSAML'
        )

        super().__init__(
            scope=scope, id=id, assumed_by=assumed_by, description=description, external_ids=external_ids, inline_policies=inline_policies,
            managed_policies=managed_policies, max_session_duration=max_session_duration, path=path, permissions_boundary=permissions_boundary
        )
