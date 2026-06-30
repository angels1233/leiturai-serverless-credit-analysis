import json
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, UTC
import os

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")

TABLE = os.environ.get("TABLE_NAME")
BUCKET = os.environ.get("BUCKET")

table = ddb.Table(TABLE)


def create_metadata(loan_id, cpf, object_key):

    table.put_item(
        Item={
            "loan_id": loan_id,
            "cpf": cpf,
            "status": "PENDING_UPLOAD",
            "object_key": object_key,
            "created_at": datetime.now(UTC).isoformat()
        }
    )


def build_response(code, body):

    return {
        "statusCode": code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(body)
    }


def lambda_handler(event, context):

    try:
        body = json.loads(event["body"])

        cpf = body["cpf_proponente"]
        nome = body["nome_arquivo"]

        loan_id = body.get(
            "loan_id",
            str(uuid.uuid4())
        )

    except Exception:

        return build_response(
            400,
            {"error": "Payload inválido"}
        )


    object_key = f"raw/{loan_id}/{nome}"

    try:

        create_metadata(
            loan_id,
            cpf,
            object_key
        )

        url = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": object_key,
                "ContentType": "application/zip",
                "Metadata": {
                    "loan_id": loan_id,
                    "cpf": cpf
                }
            },
            ExpiresIn=300
        )

        return build_response(
            200,
            {
                "loan_id": loan_id,
                "object_key": object_key,
                "upload_url": url
            }
        )

    except ClientError as e:
        print(e)

        return build_response(
            500,
            {"error": "Falha ao gerar upload"}
        )