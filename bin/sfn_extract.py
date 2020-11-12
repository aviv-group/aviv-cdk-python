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
        for k, v in tpl_raw['Parameters'].items():
            params[k] = v['Description'].split('"')[1]
            if str(k).find("S3Bucket"):
                params[k] = "cdk.out/asset||" + params[k]
        # Parse CFN template
        tpl = aws_parsecf.loads_json(json.dumps(tpl_raw), default_region='eu-west-1', parameters=params)

    # Scan resources and print out StateMachine(s)
    for k, r in tpl['Resources'].items():
        if r['Type'] != 'AWS::StepFunctions::StateMachine':
            continue
        # Fixup non existing local attributes
        definition = r['Properties']['DefinitionString']
        if definition.startswith('UNKNOWN ATT: '):
            definition = definition.replace("UNKNOWN ATT: ", "")
        if definition.endswith('.Arn'):
            definition = definition.replace(".Arn", "")
        # print("{}\n{}".format(k, definition))
        print(definition)


if __name__ == "__main__":
    cli()
