from datetime import datetime
from boto3.dynamodb.conditions import Key

def get_schedule_date_key(exact_date:datetime) -> str:
    return f"{exact_date.year}_{exact_date.month}_{exact_date.day}_{exact_date.hour}"
    
def get_subscribers_by_group(subscribers_table, group:str) -> list:
    return subscribers_table.query(KeyConditionExpression=Key('group_name').eq(group))["Items"]