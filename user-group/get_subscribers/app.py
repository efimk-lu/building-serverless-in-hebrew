import json
import boto3
from boto3.dynamodb.conditions import Key
from utils.consts import SUBSCRIBERS_TABLE
from utils.api_gw_helpers import require_group, lambda_response


# Cache client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(SUBSCRIBERS_TABLE)

@require_group
def lambda_handler(event, context):
    # Get group name
    group = event["group_name"]
    
    response = table.query(
        KeyConditionExpression=Key('group_name').eq(group)
    )
    return lambda_response(response['Items'])
   
