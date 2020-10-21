# from aws_cdk import (
#     aws_ssm as ssm,
#     aws_secretsmanager as sm,
#     core
# )

# # Outside contexts/stacks
# # app.node.try_get_context('CONTEXT_KEY')

# class dummy(core.Construct):
#     def __init__(self, scope: core.Construct, id: str):
#         super().__init__(scope, id)

#         # From SSM
#         SSMVALUE = ssm.StringParameter.value_from_lookup(self, parameter_name='/SSM/PARAM/PATH')

#         # or
#         account = '424242'
#         region = 'eu-west-1'
#         ssmp = "ssm:account={}:parameterName=/aviv/cfn/custom/layer:region={}".format(account, region)
#         self.node.try_get_context(ssmp)
#         app.node.try_get_context(ssmp)

#         # do not use unless you WANT to create a dependency between stacks
#         core.Fn.import_value('CFN_STACK_EXPORT_VALUE')
