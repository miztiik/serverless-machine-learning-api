# -*- coding: utf-8 -*-

import datetime
import json
import logging
import os
import random
import time
import urllib

import torch
from PIL import Image
from torchvision import transforms


class GlobalArgs:
    """ Global statics """
    OWNER = "Mystique"
    ENVIRONMENT = "production"
    MODULE_NAME = "greeter_lambda"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    RANDOM_SLEEP_ENABLED = os.getenv("RANDOM_SLEEP_ENABLED", False)
    ANDON_CORD_PULLED = os.getenv("ANDON_CORD_PULLED", False)


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    """ Helper to enable logging """
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


# Initial some defaults in global context to reduce lambda start time, when re-using container
logger = set_logging()


transform_test = transforms.Compose([
    transforms.Resize((600, 600), Image.BILINEAR),
    transforms.CenterCrop((448, 448)),
    transforms.ToTensor(),
    transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225)),
])

model = torch.hub.load("nicolalandro/ntsnet-cub200", "ntsnet", pretrained=True,
                       **{"topN": 6, "device": "cpu", "num_classes": 200})
model.eval()


def identify_bird(event):
    url = event["queryStringParameters"]["url"]
    _r = "IMAGE NOT REACHABLE"
    try:
        img = Image.open(urllib.request.urlopen(url))
        scaled_img = transform_test(img)
        torch_images = scaled_img.unsqueeze(0)

        with torch.no_grad():
            top_n_coordinates, concat_out, raw_logits, concat_logits, part_logits, top_n_index, top_n_prob = model(
                torch_images)

            _, predict = torch.max(concat_logits, 1)
            pred_id = predict.item()
            bird_class = model.bird_classes[pred_id]
            logger.info(f'"bird_class":"{bird_class}"')
        # return json.dumps({"bird_class": bird_class})
        _r = {"bird_class": bird_class}
    except Exception as e:
        _r = _r + f". ERROR: {str(e)}"
        logger.error(str(e))
    return _r


def lambda_handler(event, context):
    logger.info(f"rcvd_evnt:\n{event}")
    bird_data = identify_bird(event)

    return {
        "statusCode": 200,
        "body": (
            f'{{"message": "{bird_data}",'
            f'"lambda_version":"{context.function_version}",'
            f'"ts": "{str(datetime.datetime.now())}"'
            f'}}'
        )
    }
