from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_iam as _iam
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


class PytorchOnEc2Stack(core.Stack):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            vpc,
            ec2_instance_type: str,
            deploy_to_efs,
            efs_ap_ml,
            efs_sg,
            stack_log_level: str,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Read BootStrap Script):
        try:
            with open("pytorch_loader/custom_resources/stacks/bootstrap_scripts/deploy_app.sh", mode="r") as file:
                user_data = file.read()
        except OSError as e:
            print("Unable to read UserData script")
            raise e

        # Get the latest AMI from AWS SSM
        linux_ami = _ec2.AmazonLinuxImage(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

        # Get the latest ami
        amzn_linux_ami = _ec2.MachineImage.latest_amazon_linux(
            generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2)

        # ec2 Instance Role
        _instance_role = _iam.Role(
            self, "webAppClientRole",
            assumed_by=_iam.ServicePrincipal(
                "ec2.amazonaws.com"),
            managed_policies=[
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
                _iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSXRayDaemonWriteAccess"
                )
            ]
        )

        # Allow CW Agent to create Logs
        _instance_role.add_to_policy(_iam.PolicyStatement(
            actions=[
                "logs:Create*",
                "logs:PutLogEvents"
            ],
            resources=["arn:aws:logs:*:*:*"]
        ))

        # web_app_server Instance
        web_app_server = _ec2.Instance(
            self,
            "webAppServer",
            instance_type=_ec2.InstanceType(
                instance_type_identifier=f"{ec2_instance_type}"),
            instance_name="web_app_server",
            machine_image=amzn_linux_ami,
            vpc=vpc,
            vpc_subnets=_ec2.SubnetSelection(
                subnet_type=_ec2.SubnetType.PUBLIC
            ),
            block_devices=[
                _ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=_ec2.BlockDeviceVolume.ebs(
                        volume_size=50
                    )
                )
            ],
            role=_instance_role,
            user_data=_ec2.UserData.custom(
                user_data)
        )

        web_app_server.add_security_group(efs_sg)

        # Allow CW Agent to create Logs
        _instance_role.add_to_policy(
            _iam.PolicyStatement(
                actions=[
                    "logs:Create*",
                    "logs:PutLogEvents"
                ],
                resources=["arn:aws:logs:*:*:*"]
            )
        )

        ###########################################
        ################# OUTPUTS #################
        ###########################################
        output_0 = core.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = core.CfnOutput(
            self,
            "ApiConsumerPrivateIp",
            value=f"http://{web_app_server.instance_private_ip}",
            description=f"Use curl to access secure private Api. For ex, curl {{API_URL}}"
        )

        output_2 = core.CfnOutput(
            self,
            "ApiConsumerInstance",
            value=(
                f"https://console.aws.amazon.com/ec2/v2/home?region="
                f"{core.Aws.REGION}"
                f"#Instances:search="
                f"{web_app_server.instance_id}"
                f";sort=instanceId"
            ),
            description=f"Login to the instance using Systems Manager and use curl to access the SecureApiUrl"
        )
