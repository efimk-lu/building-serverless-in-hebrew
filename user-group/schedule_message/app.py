import json
import boto3
from datetime import datetime
from dacite import from_dict
import random
import string

from utils.consts import SCHEDULED_MESSAGES_TABLE, SCHEDULED_MESSAGES_BUCKET, logger
from utils.api_gw_helpers import require_group, lambda_response
from utils.general import get_schedule_date_key
from utils.models import Message

# Cache client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(SCHEDULED_MESSAGES_TABLE)

s3 = boto3.resource("s3")
bucket = s3.Bucket(SCHEDULED_MESSAGES_BUCKET)
    
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
            requested_scheduling = datetime.fromtimestamp(message.schedule_on / 1000)
            meta_data = {"group":group, "subject":message.subject, "scheduled": str(requested_scheduling), "key": key}
            logger.info(meta_data)
            bucket.put_object(Body=str.encode(body), Key=key, Metadata=meta_data)
            logger.info("S3 object saved successfully")
            response = table.put_item(
               Item={
                    "group_name": group,
                    "scheduled_date": get_schedule_date_key(requested_scheduling),
                    "message_key": key,
                    "message_added": int(datetime.now().timestamp() * 1000)
                }
            )
            logger.info("DDB object saved successfully")
            
            return lambda_response({"message":"Message scheduled successfully", "details": meta_data})
            
        except Exception as e:
            logger.error(e)
            return lambda_response({"err":"Failed saving message"}, status_code=500)