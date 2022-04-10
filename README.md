# Building Serverless application in Hebrew

## Prepare your machine
1. Install AWS SAM. Follow https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html
2. Verify it works as expected, run `sam --version` yiu should be getting something like `> SAM CLI, version 1.33.0`. Pay attention that the version might change
3. Let's initialize an Hello World for SAM example.
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
