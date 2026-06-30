import json
import os
import time
from datetime import datetime
import boto3

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ.get("TABLE_NAME"))
bda = boto3.client("bedrock-data-automation-runtime")
events = boto3.client("events")

BUCKET= os.environ.get("BUCKET")
BDA_PROJECT_ARN = os.environ.get("BDA_PROJECT_ARN")
BDA_PROFILE_ARN = os.environ.get("BDA_PROFILE_ARN")



def list_pdfs(loan_id):

    response = s3.list_objects_v2(Bucket = BUCKET, Prefix = f"raw/{loan_id}/")
    
    return [obj["Key"].split("/")[-1]
            for obj in response.get("Contents",[])
            ]

#async
def start_bda(loan_id, filename):
    
    input_uri = (f"s3://{BUCKET}/raw/{loan_id}/{filename}")

    output_uri = (f"s3://{BUCKET}/bda-output/{loan_id}")

    response = (bda.invoke_data_automation_async(
            dataAutomationProfileArn = BDA_PROFILE_ARN,
            inputConfiguration = {"s3Uri": input_uri},
            outputConfiguration = {"s3Uri": output_uri},
            dataAutomationConfiguration = {"dataAutomationProjectArn": BDA_PROJECT_ARN}
    ))
    print(response)
    return (response["invocationArn"].split("/")[-1])

def send_batch_event(loan_id, invocation_ids):
    events.put_events(Entries = [{"Source": "idp.bda", "DetailType": "bda.batch.started", "Detail":json.dumps({"loan_id": loan_id, "invocation_ids": invocation_ids}), "EventBusName": "loan-idp-bus"}])

def lambda_handler(event, context):

    detail = event["detail"]
    loan_id = detail["loan_id"]
    files = list_pdfs(loan_id)
    invocation_ids = []
    jobs = {}

    try:
        for file in files:
            print(f"Job_id:{invocation_id}")
            print("=== DEBUG BDA INPUT ===")
            print("BUCKET:", BUCKET)
            print("KEY:", key)
            print("URI:", input_uri)
            invocation_id = start_bda(loan_id, file)
            s3.head_object(Bucket=BUCKET, Key=key)
            print("S3 OK - arquivo existe e é acessível pelo Lambda")
            invocation_ids.append(invocation_id)
            jobs[file] = {"invocation_id": invocation_id, "status": "RUNNING"}
        
        #Sobrescreve metadado
        table.update_item(Key = {"loan_id": loan_id}, UpdateExpression = "SET bda_jobs = :j", ExpressionAttributeValues = {":j": jobs})
        send_batch_event(loan_id, invocation_ids)
        
    except Exception as e: 
        print(str(e))
        raise

    return {
        'statusCode': 201,
        'body': json.dumps({"Loan_id": loan_id, "invocation_ids": invocation_ids})
    }
