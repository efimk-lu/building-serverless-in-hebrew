import json
import boto3
from datetime import datetime

from utils.consts import SUBSCRIBERS_TABLE
from utils.api_gw_helpers import require_group, lambda_response

# Cache client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(SUBSCRIBERS_TABLE)

@require_group
def lambda_handler(event, context):
    # Get group name
    group = event["group_name"]
    email = json.loads(event.get("body", {})).get("email")
    if email:
        response = table.put_item(
           Item={
                "group_name": group,
                "subscriber": email,
                "date_joined": int(datetime.now().timestamp() * 1000)
            }
        )
        
        return lambda_response({"message":f"{email} added successfully"})
    
    return lambda_response({"err":"Email not found"}, status_code=500)
        
        
        
