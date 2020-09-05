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


class PytorchOnEfsStack(core.Stack):

    def __init__(
            self,
            scope: core.Construct,
            id: str,
            vpc,
            ec2_instance_type: str,
            deploy_to_efs,
            efs_share,
            efs_ap_ml,
            efs_sg,
            stack_log_level: str,
            **kwargs
    ) -> None:
        super().__init__(scope, id, **kwargs)

        # Ugly way of doing userdata
        user_data_part_01 = ("""#!/bin/bash
                        set -ex
                        EFS_MNT="/efs"
                        ML_HOME="${EFS_MNT}/ml"
                        EFS_USER_ID=1000

                        sudo yum -y install python3
                        sudo yum -y install amazon-efs-utils

                        sudo mkdir -p ${EFS_MNT}
                        """
                             )

        # Troubleshoot here
        # /var/lib/cloud/instance/scripts/part-001:
        # /var/log/user-data.log
        # file-system-id.efs.aws-region.amazonaws.com
        user_data_part_02 = f"sudo mount -t efs -o tls {efs_share.file_system_id}:/ /efs"
        user_data_part_03 = ("""
                        sudo mkdir -p ${ML_HOME}
                        cd ${ML_HOME}
                        # sudo chown ssm-user:ssm-user ${ML_HOME}
                        pip3 install -t ${ML_HOME}/lib torch
                        pip3 install -t ${ML_HOME}/lib torchvision
                        pip3 install -t ${ML_HOME}/lib numpy
                        sudo chown -R ${EFS_USER_ID}:${EFS_USER_ID} ${ML_HOME}
                        """
                             )

        user_data = user_data_part_01 + user_data_part_02 + user_data_part_03

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

        # pytorch_loader Instance
        self.pytorch_loader = _ec2.Instance(
            self,
            "pyTorchLoader",
            instance_type=_ec2.InstanceType(
                instance_type_identifier=f"{ec2_instance_type}"),
            instance_name="pytorch_loader",
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

        self.pytorch_loader.add_security_group(efs_sg)

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
            "PyTorchLoaderIp",
            value=f"http://{self.pytorch_loader.instance_private_ip}",
            description=f"Private Ip address of the server"
        )

        output_2 = core.CfnOutput(
            self,
            "PyTorchLoaderInstance",
            value=(
                f"https://console.aws.amazon.com/ec2/v2/home?region="
                f"{core.Aws.REGION}"
                f"#Instances:search="
                f"{self.pytorch_loader.instance_id}"
                f";sort=instanceId"
            ),
            description=f"Login to the instance using Systems Manager"
        )
