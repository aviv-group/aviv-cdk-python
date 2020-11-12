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
AWS_STEPFUNCTIONS_JAR_DL = os.environ.get("AWS_STEPFUNCTIONS_JAR_DL", "https://docs.aws.amazon.com/step-functions/latest/dg/samples/StepFunctionsLocal.tar.gz")

AWS_STEPFUNCTIONS_JAR = os.environ.get("AWS_STEPFUNCTIONS_JAR", "/usr/local/lib/aws/StepFunctionsLocal.jar")
# disable SAM spyware
os.environ['SAM_CLI_TELEMETRY'] = '0'

PROCESSES = []


def installJar(url: str=AWS_STEPFUNCTIONS_JAR_DL):
    if not os.path.exists(AWS_STEPFUNCTIONS_JAR):
        cdir = os.getcwd()
        os.makedirs("/usr/local/lib/aws", exist_ok=True)
        os.chdir("/usr/local/lib/aws")
        os.system('wget {}'.format(url))
        os.system('tar -xvzf StepFunctionsLocal.tar.gz')
        os.chdir(cdir)
    # check it
    os.system("java -jar {} -v".format(AWS_STEPFUNCTIONS_JAR))

def popen(cmd):
    cmd = shlex.split(cmd)
    p = subprocess.Popen(cmd)
    PROCESSES.append(p)
    return p

def getJar(path: str=AWS_STEPFUNCTIONS_JAR):
    sfnjar = path.replace("~", os.path.expanduser("~"))
    return sfnjar


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


@click.option('--template', '-t', type=click.types.STRING, default='template.json')
@click.option('--synth', '-s', help='Do a fresh cdk synth', is_flag=True, default=False)
@click.option('--sfn', '-S', help='AWS StepFunctionsLocal', is_flag=True, default=False)
@click.option('--sfn-jar', help='AWS StepFunctionsLocal.jar file path', type=click.types.STRING, default=AWS_STEPFUNCTIONS_JAR)
@click.option('--api', '-a', help='SAM local start-api', is_flag=True, default=False)
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='AWS local backends')
def daemons(template, synth, sfn, sfn_jar, api, debug):
    click.secho("=== Run local env == ", bold=True)

    click.secho("Template: {}\n\n".format(template), dim=True)

    if synth:
        os.system('cdk synth --no-staging')

    args = " --debug" if debug else ""

    popen("sam local start-lambda {} -t {}".format(args, template))
    print("SAM start-lambda: {}".format(PROCESSES[-1].pid))
    for i in range(10):
        if PROCESSES[-1].poll():
            logging.error("start-lambda FAILED pid:{}".format(PROCESSES[-1].pid))
            killAll()
            exit(42)
        time.sleep(.5)
    print("    start-lambda: {} -> {}\n".format(PROCESSES[-1].pid, PROCESSES[-1].poll()))

    if api:
        popen("sam local start-api {} -t {}".format(args, template))
        time.sleep(5)
        print("\nSAM start-api {}\n".format(PROCESSES[-1].pid))

    if sfn:
        popen('java -jar {} --lambda-endpoint {}'.format(getJar(sfn_jar), 'http://127.0.0.1:3001/'))
        time.sleep(5)
        print("\nSFN launched {}\n".format(PROCESSES[-1].pid))

    input('Hit [anykey] to kill all processes')


    for p in PROCESSES:
        p.kill()
    click.secho("\nAll done byebye!\n", bold=True)


@cli.command(short_help='Install AWS stuff locally')
def install():
    click.secho("AWS tools install and setup helper")
    click.secho("Press 'y' + [enter] to install or just [enter] to pass\n", dim=True)
    if input("- Install AWS StepFunctionsLocal? ") == 'y':
        installJar()

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
        # installJar()





@click.argument('template', type=click.types.STRING, required=True, default='template.json')
@click.option('--profile', '-p', type=click.types.STRING, default='local')
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='Run stuff locally')
def sm(template, profile, debug):
    click.secho("=== StateMachine ===")




@click.option('--template', '-t', type=click.types.STRING, default='template.json')
@click.option('--profile', '-p', type=click.types.STRING, default='local')
@click.option('--debug', '-d', is_flag=True, default=False)
@cli.command(short_help='Run stuff locally')
def run(template, profile, debug):
    click.secho("=== Local invoke ===")
    lbds = getLambdas(template)
    print("Choices:\n{}".format(
        "\n".join(["[{}] {}".format(i, l) for i, l in enumerate(lbds)])
    ))
    
    line = True
    while line != 'exit':
        line = input("AVIV AWS:run $ ")
        if line.isdigit() and lbds[int(line)]:
            os.system(
                "echo {{\"status\": \"start\"}} | sam local invoke --profile {} --template {} {}".format(
                    profile, template, lbds[int(line)]
                )
            )
            continue

        if not line:
            print("Choices:\n{}".format(
                "\n".join(["[{}] {}".format(i, l) for i, l in enumerate(lbds)])
            ))
        else:
            print("NAY: {}".format(line))

if __name__ == "__main__":
    cli()
