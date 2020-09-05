from aws_cdk import aws_apigateway as _apigw
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_logs as _logs

# from pytorch_loader.custom_resources.stacks.pytorch_loader_stack import PytorchLoaderStack

from aws_cdk import core

import uuid
import os


class GlobalArgs:
    """
    Helper to define global statics
    """

    OWNER = "MystiqueAutomation"
    ENVIRONMENT = "production"
    REPO_NAME = "serverless-machine-learning-api"
    SOURCE_INFO = f"https://github.com/miztiik/{REPO_NAME}"
    VERSION = "2020_09_03"
    MIZTIIK_SUPPORT_EMAIL = ["mystique@example.com", ]


class ServerlessMachineLearningApiStack(core.Stack):

    def __init__(
        self,
        scope: core.Construct,
        id: str,
        vpc,
        lambda_efs_sg,
        efs_sg,
        efs_share,
        efs_ap,
        efs_ap_ml,
        stack_log_level: str,
        back_end_api_name: str,
        **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Read Lambda Code):
        try:
            with open("serverless_machine_learning_api/stacks/back_end/lambda_src/bird_identifier.py",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                bird_identifier_fn_code = f.read()
        except OSError as e:
            print("Unable to read Lambda Function Code")
            raise e

        bird_identifier_fn = _lambda.Function(
            self,
            "birdIdentifierFn",
            function_name=f"bird_identifier_fn_{id}",
            runtime=_lambda.Runtime.PYTHON_3_7,
            handler="index.lambda_handler",
            code=_lambda.InlineCode(bird_identifier_fn_code),
            current_version_options={
                "removal_policy": core.RemovalPolicy.DESTROY,  # retain old versions
                "retry_attempts": 1,
                "description": "Mystique Factory Build Version"
            },
            timeout=core.Duration.minutes(5),
            memory_size=3008,
            reserved_concurrent_executions=10,
            retry_attempts=1,
            environment={
                "LOG_LEVEL": f"{stack_log_level}",
                "Environment": "Production",
                "ANDON_CORD_PULLED": "False",
                "RANDOM_SLEEP_ENABLED": "False",
                "PYTHONPATH": "/mnt/inference/lib",
                "TORCH_HOME": "/mnt/inference/model"
            },
            description="Identified the a bird in the given image(url) using pytorch",
            vpc=vpc,
            vpc_subnets=_ec2.SubnetType.PRIVATE,
            security_groups=[efs_sg],
            filesystem=_lambda.FileSystem.from_efs_access_point(
                efs_ap_ml, "/mnt/inference"),
        )

        ML_API_ALIAS = "ml-prod"

        # Create Lambda Version & Alias
        bird_identifier_fn_prod_ver = bird_identifier_fn.add_version(
            name=f"prod-{str(uuid.uuid4())}",
            description="Bird Identifier API using PyTorch running atop Lambda-EFS",
            # provisioned_executions=1,
            retry_attempts=1
        )

        bird_identifier_fn_provisioned_alias = _lambda.Alias(
            self,
            "birdIdentifierFnProdAlias",
            alias_name=f"{ML_API_ALIAS}",
            version=bird_identifier_fn_prod_ver,
            description="Bird Identifier API using PyTorch running atop Lambda-EFS"
        )

        # Create Custom Loggroup
        # /aws/lambda/function-name
        bird_identifier_fn_lg = _logs.LogGroup(
            self,
            "birdIdentifierFnLoggroup",
            log_group_name=f"/aws/lambda/{bird_identifier_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )

# %%
        wa_api_logs = _logs.LogGroup(
            self,
            "waApiLogs",
            log_group_name=f"/aws/apigateway/{back_end_api_name}/access_logs",
            removal_policy=core.RemovalPolicy.DESTROY,
            retention=_logs.RetentionDays.ONE_DAY
        )

        #######################################
        ##    CONFIG FOR API STAGE : PROD    ##
        #######################################

        # Add API GW front end for the Lambda
        prod_api_stage_options = _apigw.StageOptions(
            stage_name="prod",
            throttling_rate_limit=10,
            throttling_burst_limit=100,
            # Log full requests/responses data
            data_trace_enabled=True,
            # Enable Detailed CloudWatch Metrics
            metrics_enabled=True,
            logging_level=_apigw.MethodLoggingLevel.INFO,
            access_log_destination=_apigw.LogGroupLogDestination(wa_api_logs),
            variables={
                "lambdaAlias": f"{ML_API_ALIAS}",
                "appOwner": "Mystique"
            }
        )

        # Create API Gateway
        ml_api = _apigw.RestApi(
            self,
            "backEnd01Api",
            rest_api_name=f"{back_end_api_name}",
            deploy_options=prod_api_stage_options,
            endpoint_types=[
                _apigw.EndpointType.EDGE
            ],
            description=f"{GlobalArgs.OWNER}: API Best Practices. This stack deploys an API and integrates with Lambda $LATEST alias."
        )

        ml_api_res = ml_api.root.add_resource("ml-api")
        bird_identifier_res = ml_api_res.add_resource("identify-bird-species")

        # Add GET method to API
        bird_identifier_res_get_method = bird_identifier_res.add_method(
            http_method="GET",
            request_parameters={
                "method.request.header.InvocationType": True,
                "method.request.path.mystique": True
            },
            integration=_apigw.LambdaIntegration(
                handler=bird_identifier_fn_provisioned_alias,
                proxy=True
            )
        )

        # Outputs
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_2 = core.CfnOutput(
            self,
            "MachineLearningInferenceApiUrl",
            value=f"{bird_identifier_res.url}",
            description="Use an utility like curl from the same VPC as the API to invoke it."
        )
