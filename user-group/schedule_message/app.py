import json
import boto3
from datetime import datetime
from dataclasses import dataclass
from dacite import from_dict
import logging
import random
import string

from utils.consts import SCHEDULED_MESSAGES_TABLE, SCHEDULED_MESSAGES_BUCKET
from utils.api_gw_helpers import require_group, lambda_response

# Cache client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(SCHEDULED_MESSAGES_TABLE)

s3 = boto3.resource("s3")
bucket = s3.Bucket(SCHEDULED_MESSAGES_BUCKET)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

@dataclass(frozen=True)
class Message:
    subject:str
    body: str
    schedule_on: int
    
@require_group
def lambda_handler(event, context):
    # Get group name
    group = event["group_name"]
    body = event.get("body")
    if body is None:
        return lambda_response({"err":"Missing message details"}, status_code=500)
    else:
        try:
            message = from_dict(data_class=Message, data = json.loads(body))
            logger.info("Saving message into S3")
            key = "".join(random.choice(string.ascii_lowercase) for i in range(10))
            meta_data = {"group":group, "subject":message.subject, "scheduled": str(datetime.fromtimestamp(message.schedule_on / 1000)), "key": key}
            logger.info(meta_data)
            bucket.put_object(Body=str.encode(body), Key=key, Metadata=meta_data)
            logger.info("S3 object saved successfully")
            response = table.put_item(
               Item={
                    "group_name": group,
                    "scheduled_date": message.schedule_on,
                    "message_key": key,
                    "message_added": int(datetime.now().timestamp() * 1000)
                }
            )
            logger.info("DDB object saved successfully")
            
            return lambda_response({"message":"Message scheduled successfully", "details": meta_data})
            
        except Exception as e:
            logging.error(e)
            return lambda_response({"err":"Failed saving message"}, status_code=500)
            
    
    
        
        
        
