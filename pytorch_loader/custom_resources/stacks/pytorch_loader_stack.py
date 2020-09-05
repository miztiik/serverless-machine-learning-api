
from aws_cdk import aws_cloudformation as cfn
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_logs as _logs

from aws_cdk import core


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


class PytorchLoaderStack(core.Construct):
    def __init__(self, scope: core.Construct, id: str,
                 vpc,
                 lambda_efs_sg,
                 efs_share,
                 efs_ap_ml, ** kwargs) -> None:
        super().__init__(scope, id)

        # Read Lambda Code:)
        try:
            with open("pytorch_loader/custom_resources/stacks/lambda_src/index.py",
                      encoding="utf-8",
                      mode="r"
                      ) as f:
                pytorch_loader_fn_code = f.read()
        except OSError:
            print("Unable to read Lambda Function Code")
            raise

        # Create IAM Permission Statements that are required by the Lambda
        role_stmt1 = _iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=["*"],
            actions=[
                "dynamodb:PutItem",
                "dynamodb:DeleteItem",
                "dynamodb:UpdateItem",
            ]
        )
        role_stmt1.sid = "AllowLambdaToLoadItems"

        # Read Lambda Code):
        pytorch_loader_fn = _lambda.SingletonFunction(
            self,
            "pytorchLoaderSingleton",
            uuid=f"mystique133-0e2efcd4-3a29-e896f670",
            function_name=f"singleton_pytorch_loader_fn_{id}",
            description="Install PyTorch in EFS",
            code=_lambda.InlineCode(
                pytorch_loader_fn_code),
            handler="index.lambda_handler",
            timeout=core.Duration.seconds(20),
            runtime=_lambda.Runtime.PYTHON_3_7,
            reserved_concurrent_executions=2,
            retry_attempts=2,
            current_version_options={
                "removal_policy": core.RemovalPolicy.DESTROY,  # retain old versions
                "retry_attempts": 2,
                "description": "Mystique Factory Build Version"
            },
            environment={
                "LOG_LEVEL": "INFO",
                "APP_ENV": "Production"
            },
            vpc=vpc,
            vpc_subnets=_ec2.SubnetType.PRIVATE,
            security_groups=[lambda_efs_sg],
            filesystem=_lambda.FileSystem.from_efs_access_point(
                efs_ap_ml, "/mnt/inference")
        )

        pytorch_loader_fn.add_to_role_policy(role_stmt1)

        # Cfn does NOT do a good job in cleaning it up when deleting the stack. Hence commenting this section
        """
        # Create Custom Log group
        pytorch_loader_fn_lg = _logs.LogGroup(
            self,
            "ddb_data_loaderLogGroup",
            log_group_name=f"/aws/lambda/{pytorch_loader_fn.function_name}",
            retention=_logs.RetentionDays.ONE_WEEK,
            removal_policy=core.RemovalPolicy.DESTROY
        )
        """

        pytorch_loader = cfn.CustomResource(
            self,
            "pytorch_loaderCustomResource",
            provider=cfn.CustomResourceProvider.lambda_(
                pytorch_loader_fn
            ),
            properties=kwargs,
        )

        self.response = pytorch_loader.get_att(
            "pytorch_loader_status").to_string()
