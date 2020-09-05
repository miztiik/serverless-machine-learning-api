# -*- coding: utf-8 -*-

import json
import logging as log
import os

import boto3
import cfnresponse

log.getLogger().setLevel(log.INFO)


def install_pytorch():

    INSTALL_CMDS = (
        f"ML_MNT_PATH='/mnt/inference'"
        f"sudo yum install python3"
        f"pip install --target=${{ML_MNT_PATH}} torch torchvision numpy"
        f"sudo chown -R 1001:1001 /mnt/efs/fs1/ml"
    )


def lambda_handler(event, context):
    log.info(f"event:\n{event}")
    physical_id = 'MystiqueAutomationCustomRes'

    try:
        # MINE
        cfn_stack_name = event.get("StackId").split("/")[-2]
        resource_id = event.get("LogicalResourceId")
        res = ""
        attributes = ""

        if event["RequestType"] == "Create" and event["ResourceProperties"].get("FailCreate", False):
            log.info(f"FailCreate")
            raise RuntimeError("Create failure requested")
        if event["RequestType"] == "Create":
            res = "create_triggered"
        elif event["RequestType"] == "Update":
            res = "no_updates_made"
            pass
        elif event["RequestType"] == "Delete":
            res = "delete_triggered"
            pass
        else:
            log.error("FAILED!")
            return cfnresponse.send(event, context, cfnresponse.FAILED, attributes, physical_id)

        # MINE
        attributes = {
            "pytorch_loader_status": f"HTTPStatusCode-{res}"
        }
        cfnresponse.send(event, context, cfnresponse.SUCCESS,
                         attributes, physical_id)
    except Exception as e:
        log.exception(e)
        cfnresponse.send(event, context, cfnresponse.FAILED,
                         attributes, physical_id)
