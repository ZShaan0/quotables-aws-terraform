"""Lambda handler to get quotes and write them to S3."""

import requests
import boto3
import os
import json
import boto3
import logging
from botocore.exceptions import ClientError
from datetime import datetime as dt
from random import random, randint

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
URL = "http://api.quotable.io/quotes/random"

def lambda_handler(event, context):
    """Main handler - event is empty."""
    try:
        s3_client = boto3.client("s3")
        output_data = {"quotes": []}
        timestamp = str(int(dt.timestamp(dt.now())))
        quotes = [get_quote() for _ in range(3)]
        output_data["quotes"] = [resp for status, resp in quotes if status == 200]
        if random() < 0.1:
            quote = output_data["quotes"][randint(0, 2)]
            content = quote["content"]
            logger.info(f"[GREAT QUOTE] {content}")
        key = f"quote_{timestamp}.json"
        write_result = write_to_s3(s3_client, output_data, BUCKET_NAME, key)
        if write_result:
            logger.info("Wrote quotes to S3")
        else:
            logger.info("There was a problem. Quotes not written.")
    except Exception as e:
        logger.info(f"Unexpected Exception: {str(e)}")


def get_quote(url=URL):
    """Helper to get quote from external API."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        raw = response.json()
        required = ["content", "author", "length"]
        return (response.status_code, {k: raw[0][k] for k in required})
    except requests.HTTPError as h:
        logger.info(f"HTTP Status {response.status_code}: {str(h)}")
        formatted = {"status_message": response.json()["statusMessage"]}
        return (response.status_code, formatted)


def write_to_s3(client, data, bucket, key):
    """Helper to write material to S3."""
    body = json.dumps(data)
    try:
        client.put_object(Bucket=bucket, Key=key, Body=body)
        return True
    except ClientError as c:
        logger.info(f"Boto3 ClientError: {str(c)}")
        return False
