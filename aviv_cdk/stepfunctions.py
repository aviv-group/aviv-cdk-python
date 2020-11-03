import os
import sys
import logging
from . import __load_yaml
from aws_cdk import (
    aws_lambda,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    core
)


class Stepfunctions(core.Construct):
    statemachine: sfn.IStateMachine = None
    start: sfn.IChainable = None

    def __init__(self, scope: core.Construct, id: str, *, start: sfn.IChainable=None) -> None:
        super().__init__(scope, id)

        if not start:
            start = sfn.Pass(self, 'Pass')
        self.start = start

    def machine(self, timeout: int=1):
        self.statemachine = sfn.StateMachine(
            self, 'stateMachine',
            definition=self.start,
            timeout=core.Duration.minutes(timeout)
        )
        return self.statemachine

    def _parallel(self):
        return sfn.Parallel(
            self, 'parallel'
        )
        for branch in branches:
            self.parallel.branch(
                self._invoke(what, branch)
            )
        # return self.parallel

    def _choice(self):
        return sfn.Choice(
            self, 'choice'
        )

    def _wait(self, path:str="$.wait_time"):
        return sfn.Wait(self, 'waiter', time=sfn.WaitTime.seconds_path(path=path))

    def _invoke(self, what: str, name: str="n"):
        return sfn_tasks.LambdaInvoke(
            self, 'i_{}_{}'.format(what, name),
            lambda_function=self._function(what, name),
            output_path='$.Payload'
        )


    def _function(self, what: str, name: str, code: aws_lambda.Code=None, handler='index.handler'):
        if not code:
            code = aws_lambda.Code.inline("""import logging
import boto3

def handler(context, event):
    logging.error("{}".format(event))
    return {"status": "ok", "id": 1, "data": {"cost": 7}}
""")
        fx = aws_lambda.Function(
            self, '{}_{}'.format(what, name),
            code=code,
            handler=handler,
            runtime=aws_lambda.Runtime.PYTHON_3_7
        )
        return fx