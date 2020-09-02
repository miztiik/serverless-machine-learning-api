#!/usr/bin/env python3

from aws_cdk import core

from serverless_machine_learning_api.serverless_machine_learning_api_stack import ServerlessMachineLearningApiStack


app = core.App()
ServerlessMachineLearningApiStack(app, "serverless-machine-learning-api")

app.synth()
