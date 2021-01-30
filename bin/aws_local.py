#!/usr/bin/env python3
from os import kill
import time
import json
import os
import shlex
import subprocess
import logging
import click

# ~/.aws-sam/layers-pkg
# AWS_STEPFUNCTIONS_JAR_DL = os.environ.get("AWS_STEPFUNCTIONS_JAR_DL", "https://docs.aws.amazon.com/step-functions/latest/dg/samples/StepFunctionsLocal.tar.gz")
# AWS_STEPFUNCTIONS_JAR = os.environ.get("AWS_STEPFUNCTIONS_JAR", "/usr/local/lib/aws/StepFunctionsLocal.jar")

# disable SAM spyware
os.environ['SAM_CLI_TELEMETRY'] = '0'

PROCESSES = []


# def installJar(url: str=AWS_STEPFUNCTIONS_JAR_DL):
#     if not os.path.exists(AWS_STEPFUNCTIONS_JAR):
#         cdir = os.getcwd()
#         os.makedirs("/usr/local/lib/aws", exist_ok=True)
#         os.chdir("/usr/local/lib/aws")
#         os.system('wget {}'.format(url))
#         os.system('tar -xvzf StepFunctionsLocal.tar.gz')
#         os.chdir(cdir)
#     # check it
#     os.system("java -jar {} -v".format(AWS_STEPFUNCTIONS_JAR))

def popen(cmd, **args):
    if not 'shell' in args or args['shell'] is not True:
        cmd = shlex.split(cmd)
    p = subprocess.Popen(cmd, **args)
    PROCESSES.append(p)
    return p

# def getJar(path: str=AWS_STEPFUNCTIONS_JAR):
#     sfnjar = path.replace("~", os.path.expanduser("~"))
#     return sfnjar


def getLambdas(tpl: str):
    with open(tpl) as f:
        tpl = json.load(f)
    resources = []

    for n, r in tpl['Resources'].items():
        if r['Type'] != 'AWS::Lambda::Function':
            continue
        resources.append(n)
    return resources


def killAll():
    for p in PROCESSES:
        p.kill()
    click.secho("\nAll done byebye!\n", bold=True)


@click.group(help="Local dev helper")
def cli():
    click.secho("Aviv AWS toolkit", bold=True)


@cli.command(short_help='Install AWS stuff locally')
def install():
    click.secho("AWS tools install and setup helper")
    click.secho("Press 'y' + [enter] to install or just [enter] to pass\n", dim=True)
    # if input("- Install AWS StepFunctionsLocal Jar? ") == 'y':
    #     installJar()

    if input("- Create a fake [local] profile in ~/.aws/credentials? ") == 'y':
        print("""
cat << EOF
[local]
aws_access_key_id = __local__
aws_secret_access_key = XXXXXX
output = json
region = eu-west-1
EOF
""")

    if input("- Install AWS codebuild local? ") == 'y':
        codebuild_url = 'https://raw.githubusercontent.com/aws/aws-codebuild-docker-images/master/local_builds/codebuild_build.sh'
        os.system('cd /usr/local/bin && wget {} && chmod +x codebuild_build.sh'.format(codebuild_url))


@cli.command(short_help='AWS local codebuild')
def build():
    cbdockervs = 'aws/codebuild/standard:4.0'
    args = ' -i {} -a build/ -s .'.format(cbdockervs)
    # if os.path.exists('.env'):
    #     args += ' -e .env'
    os.system('echo codebuild_build.sh {}'.format(args))


@click.argument('template', type=click.types.STRING, default='template.json')
@click.option('--profile', '-p', type=click.types.STRING, default='local')
@click.option('--synth', '-s', help='Do a fresh cdk synth', is_flag=True, default=False)
@click.option('--sfn', '-S', help='AWS StepFunctionsLocal', is_flag=True, default=False)
# @click.option('--sfn-jar', help='AWS StepFunctionsLocal.jar file path', type=click.types.STRING, default=AWS_STEPFUNCTIONS_JAR)
@click.option('--api', '-a', help='SAM local start-api', is_flag=True, default=False)
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='AWS local backends')
def daemons(template, profile, synth, sfn, api, debug):
    click.secho(" >  SFN local StateMachine", bold=True)
    args = " --profile {}".format(profile)
    if debug:
        args += " --debug"
        click.secho("Template: {}".format(template), dim=True)
        if profile:
            click.secho("Profile: {}".format(profile), dim=True)
        print()

    if synth:
        click.secho("CDK synth refreshing templates", dim=True)
        os.system('cdk synth {} --no-staging'.format(args))
        print()

    popen("sam local start-lambda {} -t {}".format(args, template))
    click.secho("SAM local start-lambda", dim=True)
    for i in range(10):
        if PROCESSES[-1].poll():
            logging.error("start-lambda FAILED pid:{}".format(PROCESSES[-1].pid))
            killAll()
            exit(42)
        time.sleep(.5)

    if api:
        click.secho("\nStarting AWS SAM Local API...", dim=True)
        popen("sam local start-api {} -t {}".format(args, template))
        time.sleep(5)
        if PROCESSES[-1].poll():
            logging.error("sam local start-api - pid: {}\n".format(PROCESSES[-1].pid))

    if sfn:
        click.secho("\nStarting AWS SFN Local...", dim=True)
        click.secho('Hit [CTRL]-C to exit and kill all processes\n', bold=True)

        envstr = ''
        for e, v in dict(
            SAM_CLI_TELEMETRY=0,
            AWS_ACCOUNT_ID="123456789012",
            AWS_DEFAULT_REGION="us-east-1",
            LAMBDA_ENDPOINT="http://host.docker.internal:3001/").items():
            envstr += ' --env {}={}'.format(e, v)
        os.system("docker run -ti {} -p 8083:8083 amazon/aws-stepfunctions-local".format(envstr))


    for p in PROCESSES:
        p.kill()
    click.secho("\nAll done byebye!\n", bold=True)


def _help_sm():
    for i, l in enumerate(['- Create a StateMachine', '- Start it', '+ [EXECID] - Describe execution', '+ [EXECID] - Get exec. history']):
        click.secho(" [{}] {}".format(i + 1, l))
    click.secho(" [0] || [exit] - Delete StateMachine and exit", dim=True)

@click.argument('template', type=click.types.STRING, required=True, default='template.json')
@click.option('--profile', '-p', type=click.types.STRING, default='local')
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='Run stuff locally')
def sm(template, profile, debug):
    click.secho(" >  run SFN StateMachine")

    sfnargs = ' --profile {} --endpoint http://127.0.0.1:8083'.format(profile)
    if debug:
        sfnargs += " --debug"

    sfnargscreate = sfnargs + " --name localstatem --role-arn 'arn:aws:iam::123456789012:role/DummyRole'"

    # Print state machine
    smid = "arn:aws:states:us-east-1:123456789012:stateMachine:localstatem"
    execid="arn:aws:states:us-east-1:123456789012:execution:localstatem:0ade304c-9aa1-4c2f-90f0-4d86059XXXXX"

    line = ''
    while line != 'exit':
        if line == '0':
            break
        elif line == '1':
            os.system("aviv-cdk-sfn-extract {} | xargs -0 aws stepfunctions create-state-machine {} --definition ".format(
                template, sfnargscreate
            ))
        elif line == '2':
            os.system("aws stepfunctions start-execution {} --state-machine {}".format(sfnargs, smid))
            # TODO: capture SM execId (--output text | cut -f1)
            # execid='arn:local:exec'
        elif isinstance(line, str) and line.startswith('3 '):
            execid = line[2:]
            os.system("aws stepfunctions describe-execution {} --execution-arn {}".format(sfnargs, execid))
        elif isinstance(line, str) and line.startswith('4 '):
            execid = line[2:]
            os.system("aws stepfunctions get-execution-history {} --execution-arn {}".format(sfnargs, execid))
        else:
            _help_sm()
        line = input("AVIV AWS:sm $ ")

    os.system("aws stepfunctions delete-state-machine {} --state-machine-arn {}".format(sfnargs, smid))
    click.secho("\nAll gone byebye!", dim=True)


def _help_run(lambdas: list):
    print("Run Lambda:")
    for i, l in enumerate(lambdas):
        print(" [{}] - {}".format(i + 1, l))
    click.secho(" [0] || [exit] - Exit", dim=True)

@click.argument('template', type=click.types.STRING, required=True, default='template.json')
@click.option('--profile', '-p', type=click.types.STRING, default='local')
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='Run stuff locally')
def run(template, profile, debug):
    click.secho("=== Local invoke ===")
    lbds = getLambdas(template)
    
    line = ''
    while line != 'exit':
        if line == '0':
            break
        elif line.isdigit() and lbds[int(line) - 1]:
            os.system("echo {{\"status\": \"start\"}} | sam local invoke --profile {} --template {} {}".format(
                profile, template, lbds[int(line) - 1]
            ))
        else:
            _help_run(lbds)
        line = input("AVIV AWS:run $ ")

    click.secho("\nAll gone byebye!", dim=True)

if __name__ == "__main__":
    cli()
