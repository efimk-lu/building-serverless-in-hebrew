import json
import boto3
from boto3.dynamodb.conditions import Key


# Cache client
dynamodb = boto3.resource("dynamodb")
SUBSCRIBERS_TABLE = "subscribers"
def lambda_handler(event, context):
    # Get group name
    group = event.get("pathParameters", {}).get("group")
    if group:
        table = dynamodb.Table(SUBSCRIBERS_TABLE)
        response = table.query(
            KeyConditionExpression=Key('group_name').eq(group)
        )
        return {
            "statusCode": 200,
            "body": json.dumps(response['Items']),
        }
    else:
        return {
            "statusCode": 500,
            "body": "Missing group!",
        }
