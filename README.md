# Building Serverless application in Hebrew

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
        HelloWorld:
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
