import sys
sys.path.append('/opt')  # nopep8
import logging

def handler(request, context):
  logging.warning(request)

  import requests
  import boto3
  from botocore.exceptions import ClientError
  from cfn_resource_provider import ResourceProvider

  class SAMLProvider(ResourceProvider):
    """
    Generic Cloudformation custom resource provider for Auth0 resources.
    from https://github.com/binxio/cfn-saml-provider
    """
    def __init__(self):
      super(SAMLProvider, self).__init__()
      self.request_schema = {
        "type": "object",
        "oneOf": [
          {
          "properties": {
            "Name": {"type": "string","description": "of the saml provider"},
            "Metadata": {"type": "string", "description": "of the saml provider"}
          },
          "required": ["Name", "Metadata"]
          },
          {
          "properties": {
            "Name": {"type": "string", "description": "of the saml provider"},
            "URL": { "type": "string", "description": "pointing to the SAML Metadata Document"}
          },
          "required": ["Name", "URL"]
          }
        ]
      }
      self.iam = boto3.client('iam')

    @property
    def custom_cfn_resource_name(self):
      return 'Custom::SAMLProvider'

    def get_metadata(self):
      logging.warning("RP: {}".format(self.properties))
      metadata = self.get('Metadata', None)
      if metadata != None:
        return None, metadata
      try:
        response = requests.get(self.get('URL'))
        metadata = response.text
        if response.status_code == 200:
          return None, metadata
      except requests.exceptions.RequestException as e:
        return '{}'.format(e), None

      return 'url %s returned status code %d, %s'.format(self.get('URL'), response.status_code, response.text), None

    def create(self):
      err, metadata = self.get_metadata()
      if err:
        self.physical_resource_id = 'could-not-create'
        self.fail(err)
        return
      try:
        response = self.iam.create_saml_provider(Name=self.get('Name'), SAMLMetadataDocument=metadata)
        self.physical_resource_id = response['SAMLProviderArn']
      except ClientError as e:
        self.physical_resource_id = 'could-not-create'
        self.fail('{}'.format(e))

    def update(self):
      err, metadata = self.get_metadata()
      if err:
        self.fail(err)
        return
      try:
        response = self.iam.update_saml_provider(SAMLProviderArn=self.physical_resource_id, SAMLMetadataDocument=metadata)
        self.physical_resource_id = response['SAMLProviderArn']
      except ClientError as e:
        self.fail('{}'.format(e))

    def delete(self):
      import re
      if re.match(r'arn:aws[-a-z]*:iam::[0-9]*:saml-provider/.*$', self.physical_resource_id):
        try:
          response = self.iam.delete_saml_provider(SAMLProviderArn=self.physical_resource_id)
          self.physical_resource_id = response['SAMLProviderArn']
        except ClientError as e:
          self.fail('{}'.format(e))

  provider = SAMLProvider()
  return provider.handle(request, context)
