import json
import boto3
from datetime import datetime
from boto3.dynamodb.conditions import Key
from typing import List
from dacite import from_dict
from utils.models import Message

from utils.consts import SCHEDULED_MESSAGES_TABLE, SUBSCRIBERS_TABLE, SCHEDULED_MESSAGES_BUCKET, logger, SOURCE_EMAIL
from utils.general import get_schedule_date_key, get_subscribers_by_group

# Cache client
dynamodb = boto3.resource("dynamodb")
scheduled_messages_table = dynamodb.Table(SCHEDULED_MESSAGES_TABLE)
subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)
s3 = boto3.resource("s3")
ses_client = boto3.client('ses')

def lambda_handler(event, context):
    try:
        now = datetime.now()
        logger.info("Checking in DB for relevant messages")
        responses = scheduled_messages_table.query(KeyConditionExpression=Key('scheduled_date').eq(get_schedule_date_key(now)))["Items"]
        messages_to_send = [response for response in responses if response.get("sent") is None ]
        logger.info(f"Found {len(messages_to_send)} messages")
        _send_email_to_subscribers(messages_to_send, s3, SCHEDULED_MESSAGES_BUCKET)
        
        if len(messages_to_send) > 0:
            logger.info("Emails sent successfully")
        
        for item in messages_to_send:
            scheduled_messages_table.update_item(
                Key={
                    "scheduled_date": get_schedule_date_key(now),
                    "group_name": item["group_name"]
                },
                UpdateExpression="SET sent=:sent",
                ExpressionAttributeValues={
                    ":sent": True
                },
            )
            logger.info(f"Marked {get_schedule_date_key(now)} for {item['group_name']} as sent")
    
        
    except Exception as e:
        logger.error(e)
        raise e
            
    
    
def _get_s3_content(s3, bucket:str, key:str):
    response = s3.Object(SCHEDULED_MESSAGES_BUCKET, key).get()
    return response["Body"].read()
    
def _send_email(subscribers:List[str], content:Message):
    logger.info(f"Sending {len(subscribers)} emails")
    ses_client.send_email(Source=SOURCE_EMAIL, Destination= {"BccAddresses": subscribers}, Message={
        "Body": {
            "Html": {
                "Charset": "UTF-8",
                "Data": content.body,
            }
        },
        "Subject": {
            "Charset": "UTF-8",
            "Data": content.subject,
        },
    },)
    
        
def _send_email_to_subscribers(scheduled_messages:List[dict], s3, bucket:str):
    for message in scheduled_messages:
        subscribers = get_subscribers_by_group(subscribers_table, message["group_name"])
        logger.info(subscribers)
        content = from_dict(data_class=Message, data = json.loads(_get_s3_content(s3, bucket, message["message_key"])))
        _send_email([subscriber["subscriber"] for subscriber in subscribers], content)
        
        
