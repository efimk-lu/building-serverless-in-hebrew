# Building Serverless application in Hebrew

- [Prepare your machine](#prepare-your-machine)
  * [Hello SAM](#hello-sam)
- [Step 1 - Implement get-subscribers](#step-1---implement-get-subscribers)
- [Step 2 - Implement add-subscriber](#step-2---implement-add-subscriber)
- [Step 3 - Schedule a message](#step-3---schedule-a-message)
- [Step 4 - Send a message](#step-4---send-a-message)
- [Testing](#testing)

<small><i><a href='http://ecotrust-canada.github.io/markdown-toc/'>Table of contents generated with markdown-toc</a></i></small>
 
## Prepare your machine
1. Install AWS SAM. Follow https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
2. Verify it works as expected, run `sam --version` yiu should be getting something like `> SAM CLI, version 1.33.0`. Pay attention that the version might change
3. Let's initialize an Hello World for SAM example. If it works, then your machine is ready.
### Hello SAM
1. `sam init`
2. Choose `AWS Quick Start Templates`
3. Choose `Zip`
4. Choose `Python 3.9`
5. For project name, choose the default
6. Choose `Hello World Example` template
7. You need to build the sam packge 
8. Go to the folder the template created `cd sam-app`
9. Run `sam build` and next run `sam deploy --guided`. You should run guided each time you want to add something to the sam configuration file or create it for the first time.
10. When asked `Confirm changes before deploy` choose `y`
11. When asked `HelloWorldFunction may not have authorization defined, Is this okay?` choose `y`
12. The rest can be defaults
13. `Deploy this changeset?` choose `y`
14. Give the deployment a try, you should see under `Outputs` the `API Gateway endpoint URL`, copy the URL and try it on browser.

**Wait for the instructor to go over the directory structure of a SAM application.**

## Step 1 - Implement get-subscribers
1. Clone `git@github.com:efimk-lu/building-serverless-in-hebrew.git`
2. Checkout the `base` tag , e.g. `git checkout tags/base` 
3. You should see a basic structure of our SAM aplication for managing user groups.
4. Rename folder `add_subscriber`  --> `get-subscribers`
5. Add `boto3==1.21.37` to `requirements.txt`
6. Paste 
```
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
```
into `app.py`

7. Paste
```
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: >
  user-group
  User group functionality
# More info about Globals: https://github.com/awslabs/serverless-application-model/blob/master/docs/globals.rst
Globals:
  Function:
    Timeout: 3

Resources:
  GetSubscribersFunction:
    Type: AWS::Serverless::Function 
    Properties:
      CodeUri: get_subscribers/
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Policies:
        - DynamoDBReadPolicy:
            TableName:
              !Ref SubscribersTable
      
      Events:
        Subscribers:
          Type: Api 
          Properties:
            Path: /{group}/subscribers
            Method: get
  
  SubscribersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: "subscribers"
      AttributeDefinitions: 
        - 
          AttributeName: "group_name"
          AttributeType: "S"
        - 
          AttributeName: "subscriber"
          AttributeType: "S"
      KeySchema: 
        - 
          AttributeName: "group_name"
          KeyType: "HASH"
        - 
          AttributeName: "subscriber"
          KeyType: "RANGE"
      BillingMode: PAY_PER_REQUEST
Outputs:
  HelloWorldApi:
    Description: "API Gateway endpoint URL for Prod stage for Hello World function"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/{group}/subscribers"
```
into `template.yaml`

8. Build and deploy `sam build`
9. `sam deploy --guided`. Use `user-groups` as stack name

## Step 2 - Implement add-subscriber
1. Duplicate `get_subscribers` and rename the new folder `add_subscriber`
2. Paste
```
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
```
into `app.py`

3. Create a `utils` python package
4. Paste 
```
import json 
from typing import Callable, Any, Optional, List, Dict, Union

def lambda_response(
    content: Any,
    status_code: int = 200,
    content_type: str = "application/json",
) -> dict:
    """
    Returns a dictionary that adheres to the required format that is needed by AWS api gw ->> Lambda proxy integration.
    See https://aws.amazon.com/premiumsupport/knowledge-center/malformed-502-api-gateway/ for more details
    :param content: The actual content that needs to return
    :param status_code: The status code of the response. In case of an exception, you can use a more specialized method
    :param content_type: The Content-Type header value of the response.
    :param should_gzip: Should the content be compressed.
    """

    try:
        body_message = (
            json.dumps(content, default=str) if content_type == "application/json" else content
        )
    except Exception as err:
        print(f"Invalid lambda response. {err}")

        status_code = 500
        body_message = "Err"
    response = {
        "statusCode": str(status_code),
        "body": body_message,
        "headers": {
            "Content-Type": content_type,
        },
    }

    return response


def require_group(function):
    def wrapper(*args, **kwargs):
        event = args[0]
        if type(event).__name__ != "dict":
            return function(*args, **kwargs)

        group = event.get("pathParameters", {}).get("group")
        if group:
            event["group_name"] = group
            return function(*args, **kwargs)
        else:
            return {
                "statusCode": 500,
                "body": "Missing group!",
            }

    return wrapper
```
into `user-group/utils/api_gw_helpers.py`

5. Paste `SUBSCRIBERS_TABLE = "subscribers"` into `user-group/utils/consts.py`
6. Add
```
AddSubscriberFunction:
    Type: AWS::Serverless::Function 
    Properties:
      CodeUri: add_subscriber/
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Policies:
        - DynamoDBWritePolicy:
            TableName:
              !Ref SubscribersTable

      Events:
        Subscribers:
          Type: Api 
          Properties:
            Path: /{group}/subscribers
            Method: post
```
to `user-group/template.yaml` under `Resources`

7. Simplify `user-group/get_subscribers/app.py`
```
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
```
8. Link `utils` in each one of the functions. 
`cd get_subscribers && ln -s ../utils`
and
`cd add_subscriber && ln -s ../utils`
9. `sam build && sam deploy`
10. Test it using curl
```
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/serverless/subscribers -H 'Content-Type: application/json' -d '{"email":"efi@lumigo.io"}'
curl https://<api-d>.execute-api.us-east-1.amazonaws.com/Prod/serverless/subscribers
```
Replace **api-id** with the relevent code you can copy from the output 

## Step 3 - Schedule a message
1. Duplicate `get_subscribers` and rename the new folder `schedule_message`
2. Paste
```
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
```
into `app.py`

3. Paste
```
boto3==1.21.37
dacite==1.6.0
```
into `user-group/schedule_message/requirements.txt`

4. Add to `user-group/template.yaml`
Under Resources
```
ScheduleFunction:
    Type: AWS::Serverless::Function 
    Properties:
      CodeUri: schedule_message/
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Policies:
        - DynamoDBWritePolicy:
            TableName:
              !Ref ScheduledMessagesTable
        - S3WritePolicy:
            BucketName:
              !Ref ScheduledMessagesBucket

      Environment:
        Variables:
          SCHEDULED_MESSAGES_BUCKET_NAME: !Ref ScheduledMessagesBucket
      Events:
        Subscribers:
          Type: Api 
          Properties:
            Path: /{group}/schedule
            Method: post
```

Add new S3 bucket definition
```
ScheduledMessagesBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${ScheduledMessagesBucketName}"
```

Add a new table definition
```
ScheduledMessagesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: "scheduled_messages"
      AttributeDefinitions: 
        - 
          AttributeName: "group_name"
          AttributeType: "S"
        - 
          AttributeName: "scheduled_date"
          AttributeType: "N"
      KeySchema: 
        - 
          AttributeName: "group_name"
          KeyType: "HASH"
        - 
          AttributeName: "scheduled_date"
          KeyType: "RANGE"
      BillingMode: PAY_PER_REQUEST
```
Define a new `Parameters` section above `Resources`
```
Parameters:
  ScheduledMessagesBucketName:
    Type: String
```

Replace the `Outputs` section
```
Outputs:
  SubscribersList:
    Description: "API Gateway endpoint URL getting the subscribers"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/{group}/subscribers"
    
  ScheduleMessage:
    Description: "API Gateway endpoint URL for scheduling a message"
    Value: !Sub "https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod/{group}/schedule"
```

4. Paste 
```
import os

SUBSCRIBERS_TABLE = "subscribers"
SCHEDULED_MESSAGES_TABLE = "scheduled_messages"
SCHEDULED_MESSAGES_BUCKET = os.environ.get("SCHEDULED_MESSAGES_BUCKET_NAME") 
```
into `user-group/utils/consts.py`

5. S3 bucket name is unique across AWS, therefore the bucket name is defined as an external parameter, which should contain a different value for each one of you.

Rerun `sam build && sam deploy --guided`, give `ScheduledMessagesBucketName` a unique name, for example `myname-randomstr`

make sure you answer `y` for all `... may not have authorization defined, Is this okay?` questions

6. Test it using curl
`curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/serverless/schedule -H 'Content-Type: application/json' -d '{"subject":"Hello SLS workshop!", "body":"The workshop is not recorded.<h1>Welcome dear friends</h1>", "schedule_on":1649753447000}'`
7. Search for the file on the S3 bucket and the record in DynamoDB.

## Step 4 - Send a message
1. We will change the DynamoDB schema definition. DynamoDB does not support it, threfore we need to delete the current stack.
2. The deletion will fail becuase you've created an S3 bucket. You have to delete it manually. Go to the S3 console, choose your bucket, click on `Empty` and then `Delete`
3. Run `sam delete`, choose `y` whenever possible.
4. Duplicate `get_subscribers` and rename the new folder `send_scheduled_messages`
5. Paste
```
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
```
into `app.py`

6. Paste
```
boto3==1.21.37
dacite==1.6.0
```
into `user-group/send_scheduled_messages/requirements.txt`

7. Paste
```
from datetime import datetime
from boto3.dynamodb.conditions import Key

def get_schedule_date_key(exact_date:datetime) -> str:
    return f"{exact_date.year}_{exact_date.month}_{exact_date.day}_{exact_date.hour}"

def get_subscribers_by_group(subscribers_table, group:str) -> list:
    return subscribers_table.query(KeyConditionExpression=Key('group_name').eq(group))["Items"] 
```
into `user-group/utils/general.py`

8. Paste
```
from dataclasses import dataclass

@dataclass(frozen=True)
class Message:
    subject:str
    body: str
    schedule_on: int 
```
into `user-group/utils/models.py`

9. Add
```
import logging

# previous stuff

SOURCE_EMAIL = os.environ.get("SOURCE_EMAIL")

logger = logging.getLogger()
logger.setLevel(logging.INFO) 
```
to `user-group/utils/consts.py`

10. Paste
```
import json
import boto3
from boto3.dynamodb.conditions import Key
from utils.consts import SUBSCRIBERS_TABLE
from utils.api_gw_helpers import require_group, lambda_response
from utils.general import get_subscribers_by_group

# Cache client
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(SUBSCRIBERS_TABLE)

@require_group
def lambda_handler(event, context):
    # Get group name
    group = event["group_name"]
    
    return lambda_response(get_subscribers_by_group(table, group))
```
into `user-group/get_subscribers/app.py`

11. Paste
```
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
```
into `user-group/schedule_message/app.py`

12. Add to `user-group/template.yaml`
```
SendScheduledMessagesFunction:
    Type: AWS::Serverless::Function 
    Properties:
      CodeUri: send_scheduled_messages/
      Handler: app.lambda_handler
      Runtime: python3.9
      Architectures:
        - x86_64
      Policies:
        - DynamoDBCrudPolicy:
            TableName:
              !Ref ScheduledMessagesTable
        - DynamoDBReadPolicy:
            TableName:
              !Ref SubscribersTable
        - S3ReadPolicy:
            BucketName:
              !Ref ScheduledMessagesBucket

      Environment:
        Variables:
          SCHEDULED_MESSAGES_BUCKET_NAME: !Ref ScheduledMessagesBucket
          SOURCE_EMAIL: !Ref SourceEmail
      Events:
        MessageRule:
          Type: Schedule
          Properties:
            Schedule: 'rate(1 hour)'
            Name: MessageRule
```
Under the `Resources` section 


Add
```
SourceEmail:
    Type: String
```
under the `Parameters` section

Replace `ScheduledMessagesTable` with 

```
ScheduledMessagesTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: "scheduled_messages"
      AttributeDefinitions: 
        - 
          AttributeName: "group_name"
          AttributeType: "S"
        - 
          AttributeName: "scheduled_date"
          AttributeType: "S"
      KeySchema: 
        - 
          AttributeName: "scheduled_date"
          KeyType: "HASH"
        - 
          AttributeName: "group_name"
          KeyType: "RANGE"
      BillingMode: PAY_PER_REQUEST
```

13. Let's deploy it `sam build && sam deploy --guided`. Make sure to define `SourceEmail` parameter to your email
14. Next you need to verify your email (the one you defined at step #13) under the SES service. Follow https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#verify-email-addresses-procedure
15. You are ready to test it

## Testing
1. Let's make sure your email is subscribed to the `serverless` group.
```
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/serverless/subscribers -H 'Content-Type: application/json' -d '{"email":"efi@lumigo.io"}'

curl https://<ap-id>.execute-api.us-east-1.amazonaws.com/Prod/serverless/subscribers
```
2. Let's schedule a message for this hour. For the timestamp use https://www.epochconverter.com/
```
curl -X POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/serverless/schedule -H 'Content-Type: application/json' -d '{"subject":"Hello SLS workshop!", "body":"The workshop is not recorded.<h1>Welcome dear friends</h1>", "schedule_on":<epoch including milliseconds>}'
```
3. We can wait for the `SendScheduledMessagesFunction` Lambda to be triggered, but let's try to run it manually.
4. Go the AWS Lambda console, click on the `Test` tab, choose the default values and click on `Save.
<img width="1618" alt="image" src="https://user-images.githubusercontent.com/43570637/162713355-e8fc83a0-a406-43d0-8618-75ea67c658ef.png">
5. You should be getting a permission error
<img width="1624" alt="image" src="https://user-images.githubusercontent.com/43570637/162713582-464565ab-4080-4954-85be-c15a9e346931.png">

6. Let's add the missing permission. Add
```
SESCrudPolicy:
    IdentityName:
        !Ref SourceEmail
```
Under policies for the `SendScheduledMessagesFunction` Lambda

7. Redeploy (build & deploy)
8. A successful message was sent to your subscribers
<img width="1534" alt="image" src="https://user-images.githubusercontent.com/43570637/162719901-b1e78145-3050-44d4-bcfa-95b8deec3fc7.png">
