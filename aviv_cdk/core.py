import os
import subprocess
import typing
import constructs
from aws_cdk import (
    aws_ssm,
    core
)
# from aws_cdk.core import Stack, Environment, App, Construct

# Disable SAM spyware, should be opt-in
os.environ['SAM_CLI_TELEMETRY'] = '0'

class Stack(core.Stack):
    def __init__(
        self,
        scope: typing.Optional[constructs.Construct]=None,
        id: typing.Optional[str]=None, *,
        analytics_reporting: typing.Optional[bool]=None,
        description: str=None,
        env: core.Environment=None,
        stack_name: str=None,
        synthesizer: core.IStackSynthesizer=None,
        tags: typing.Mapping[str, str]=None,
        termination_protection: bool=False) -> None:

        super().__init__(
            scope,
            id,
            analytics_reporting=analytics_reporting,
            description=description,
            env=env,
            stack_name=stack_name,
            synthesizer=synthesizer,
            tags=tags,
            termination_protection=termination_protection
        )


class Environment(core.Environment):
    name: str
    def __init__(self, account: str=None, region: str='eu-west-1', name: str=None) -> None:
        self.name = name
        super().__init__(account=account, region=region)


class App(core.App):
    def __init__(
        self,
        analytics_reporting: typing.Optional[bool]=False,  # This should be opt-in
        auto_synth: typing.Optional[bool]=None,
        context: typing.Optional[typing.Mapping[str, typing.Any]]=None,
        outdir: typing.Optional[str]=None,
        runtime_info: typing.Optional[bool]=None,
        stack_traces: typing.Optional[bool]=None,
        tree_metadata: typing.Optional[bool]=None) -> None:

        super().__init__(
            analytics_reporting=analytics_reporting,
            auto_synth=auto_synth,
            context=context,
            outdir=outdir,
            runtime_info=runtime_info,
            stack_traces=stack_traces,
            tree_metadata=tree_metadata
        )


def ssm_lookup(scope, parameter_name):
    return aws_ssm.StringParameter.value_from_lookup(scope, parameter_name=parameter_name)


def auto_github():
    dirp = os.path.dirname(os.path.dirname(__file__))
    # os.chdir(dirp)

    # output = subprocess.check_output("pwd; ls -la", shell=True)
    # print(output)
    repo_dir = subprocess.Popen(['git', 'rev-parse', '--show-toplevel'], stdout=subprocess.PIPE).communicate()  #[0].rstrip()
    print(str(repo_dir[0].decode('UTF-8')))

    output = subprocess.check_output("git name-rev --name-only HEAD", shell=True)

    print("got: {}".format(output))
