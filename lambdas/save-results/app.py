import json
import boto3
import os
from datetime import datetime, UTC

#Cliente
bd_nova = boto3.client("bedrock-runtime")
s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ.get("TABLE_NAME"))

BUCKET = os.environ.get("BUCKET")

def get_metadado(loan_id):

    response = table.get_item(Key = {"loan_id": loan_id})
    
    return response["Item"]

#Carregamento dos JSON
def laod_results(loan_id, invocation_ids):

    documents = []

    for invocation_id in invocation_ids:
        key = (f"bda-output/"f"{loan_id}/"f"{invocation_id}/"f"0/custom_output/0/"f"result.json")

        try:
           print("Lendo:",key)
           obj = s3.get_object(Bucket = BUCKET, Key = key)
           raw = json.loads(obj["Body"].read().decode())
           documents.append({"invocation_id": invocation_id, "text": raw.get("text"), "entities": raw.get("entities")})

        except Exception as e:
            print("Ignorado:", key, str(e))
            
    return documents


def invoke_nova(documents):

    prompt = {
        "messages": [
            {
                "role": "user",

                "content": [
                    {
                        "text": f"""
Você recebe vários JSON extraídos pelo Amazon Bedrock Data Automation.

Objetivos:

1 Consolidar.

2 Remover duplicados.

3 Não inventar.

4 Campo ausente → null.

5 Produzir JSON único.

Documentos: {json.dumps(documents)}
"""
                    }
                ]
            }
        ] 
    }

    response = bd_nova.invoke_model(modelId = "amazon.nova-pro-v1:0", body =json.dumps(prompt), contentType ="application/json", accept = "application/json")
    raw = (response["body"].read().decode("utf-8"))

    return json.loads(raw)

def save_normalized(loan_id,result):
    key = (f"normalized/"f"{loan_id}.json")
    s3.put_object(Bucket = BUCKET, Key = key, Body = json.dumps(result, indent=2), ContentType = "application/json")

    return key 

def finish_process(loan_id, key):
    table.update_item(Key={"loan_id": loan_id}, UpdateExpression =""" SET #s = :s, normalized_path = :k, normalized_at = :t""",ExpressionAttributeNames = {"#s": "status"}, ExpressionAttributeValues = {":s": "NORMALIZED", ":k": key, ":t":datetime.now(UTC).isoformat()})


def lambda_handler(event, context):

    print(json.dumps(event))
    detail = event["detail"]
    loan_id = detail["loan_id"]

    invocation_ids = (detail["invocation_ids"])
    print("loan:", loan_id)

    documents = laod_results(loan_id, invocation_ids)

    if not documents:
        raise Exception("Nenhum resultado encontrado")
    print(f"{len(documents)} carregados")

    normalized = (invoke_nova(documents))

    output = (save_normalized(loan_id,normalized))

    finish_process(loan_id, output)
   
    
    return {
        'statusCode': 201,
        'body': json.dumps({"loan_id": loan_id, "output": output})
    }