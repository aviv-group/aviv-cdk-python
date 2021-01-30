#!/usr/bin/env python3
import click
import json
from aws_parsecf.functions import Functions
# whatever...
Functions.REF_PSEUDO_FUNCTIONS['AWS::Partition'] = lambda self: 'aws'
import aws_parsecf


@click.argument('template', type=click.types.STRING, required=True, default='template.json')
@click.command(short_help='Extract an AWS StepFunctions StateMachine from a CDK/CFN template')
def cli(template: str):
    with open(template, 'r') as f:
        # Extract and generate CFN template parameters
        tpl_raw = json.load(f)
        params = dict()

        # Cleanup CDK specific stuff
        if 'Rules' in tpl_raw and 'CheckBootstrapVersion' in tpl_raw['Rules']:
            del tpl_raw['Rules']['CheckBootstrapVersion']
        if 'Parameters' in tpl_raw and 'BootstrapVersion' in tpl_raw['Parameters']:
            del tpl_raw['Parameters']['BootstrapVersion']

        for k, v in tpl_raw['Parameters'].items():
            if 'Description' in v and v['Description'].find('"') >= 0:
                params[k] = v['Description'].split('"')[1]
            if str(k).find("S3Bucket") >= 0:
                params[k] = "cdk.out/asset||" + params[k]
        # Parse CFN template
        tpl = aws_parsecf.loads_json(json.dumps(tpl_raw), default_region='eu-west-1', parameters=params)

    # Scan resources and print out StateMachine(s)
    for k, r in tpl['Resources'].items():
        if r['Type'] != 'AWS::StepFunctions::StateMachine':
            continue
        # Fixup non existing local attributes
        definition = r['Properties']['DefinitionString'].replace("UNKNOWN ATT: ", "").replace(".Arn", "")
        # print("{}\n{}".format(k, definition))
        print(definition)


if __name__ == "__main__":
    cli()
