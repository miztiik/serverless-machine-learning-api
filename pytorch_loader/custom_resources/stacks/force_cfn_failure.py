
import requests
import json
responseUrl = "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/arn%3Aaws%3Acloudformation%3Aus-east-1%3A230023004178%3Astack/serverless-machine-learning-api/e8809510-ee1b-11ea-850b-0a5afd1032bb%7CpytorchLoaderpytorchloaderCustomResourceFF045030%7Cc999ab51-962e-43d1-8671-70c28e505ba6?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20200903T193534Z&X-Amz-SignedHeaders=host&X-Amz-Expires=7200&X-Amz-Credential=AKIA6L7Q4OWTXGMS66PD%2F20200903%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=e7316da2aeb9061df453f44f9e4553960bf04cd8be4d0f662df6565d44901717"

responseBody = {
    "Status": "FAILED",
    "Reason": "See the details in CloudWatch Log Stream: 2020/09/03/[$LATEST]4857498c377f4d5ba3fe4bf28d51dc75",
    "PhysicalResourceId": "MystiqueAutomationCustomRes",
    "StackId": "arn:aws:cloudformation:us-east-1:230023004178:stack/serverless-machine-learning-api/e8809510-ee1b-11ea-850b-0a5afd1032bb",
    "RequestId": "c999ab51-962e-43d1-8671-70c28e505ba6",
    "LogicalResourceId": "pytorchLoaderpytorchloaderCustomResourceFF045030",
    "NoEcho": False,
    "Data": {
        "pytorch_loader_status": "HTTPStatusCode-create_triggered"
    }
}
json_responseBody = json.dumps(responseBody)
headers = {
    'content-type': '',
    'content-length': str(len(json_responseBody))
}
response = requests.put(responseUrl,
                        data=json_responseBody,
                        headers=headers)
print("Status code: " + response.reason)
