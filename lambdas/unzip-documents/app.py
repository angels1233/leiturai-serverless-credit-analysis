import json
import boto3
import os
import tempfile
import zipfile
from urllib.parse import unquote_plus
from datetime import datetime, UTC

ddb = boto3.resource("dynamodb")
s3 = boto3.client("s3")
events = boto3.client("events")

TABLE_NAME = os.environ.get("TABLE_NAME")
table = ddb.Table(TABLE_NAME)
BUCKET = "bucket-s3-grupo11-hack2hire-2026"
EVENT_BUS = "loan-idp-bus"

def create_metadata(loan_id, total_documents):
    """Cria metadado no DynamoDB"""
    try:
        table.put_item(
            Item={
                "loan_id": loan_id,
                "SK": "PROCESS",
                "status": "UPLOADED",
                "expected_documents": total_documents,
                "processed_documents": 0,
                "bda_jobs": {},
                "created_at": datetime.now(UTC).isoformat()
            }
        )
        print(f"Metadado criado: loan_id={loan_id}, total={total_documents}")
        return True
    except Exception as e:
        print(f"Erro ao criar metadado: {e}")
        return False

def list_directory_contents(directory):
    """Lista todo o conteudo de um diretorio recursivamente"""
    print(f"Conteudo do diretorio: {directory}")
    for root, dirs, files in os.walk(directory):
        print(f"  Pasta: {root}")
        for file in files:
            print(f"    Arquivo: {file}")
        for dir_name in dirs:
            print(f"    Subpasta: {dir_name}")

def find_pdfs_in_dir(directory):
    """Percorre recursivamente um diretorio e encontra todos os PDFs"""
    pdf_files = []
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(".pdf"):
                file_path = os.path.join(root, file)
                pdf_files.append({
                    "file_name": file,
                    "file_path": file_path,
                    "base_name": file
                })
                print(f"PDF encontrado: {file_path}")
    
    return pdf_files

def process_zip(bucket, key, loan_id):
    """Processa arquivo ZIP"""
    print(f"=== PROCESSANDO ZIP ===")
    print(f"Bucket: {bucket}")
    print(f"Key: {key}")
    print(f"loan_id: {loan_id}")
    
    pdf_files = []
    uploaded = []
    
    # Cria o diretorio temporario
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "file.zip")
        
        # Baixa ZIP
        print(f"Baixando ZIP: s3://{bucket}/{key}")
        try:
            s3.download_file(bucket, key, zip_path)
            print(f"ZIP baixado com sucesso: {zip_path}")
            
            # Verifica o tamanho do arquivo
            zip_size = os.path.getsize(zip_path)
            print(f"Tamanho do ZIP: {zip_size} bytes")
            
            if zip_size == 0:
                print("ERRO: ZIP vazio!")
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "ZIP vazio"})
                }
                
        except Exception as e:
            print(f"Erro ao baixar ZIP: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Erro ao baixar ZIP: {str(e)}"})
            }
        
        # Extrai ZIP
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Lista todos os arquivos do ZIP
                print("Conteudo do ZIP:")
                for name in zip_ref.namelist():
                    print(f"  - {name}")
                
                # Extrai tudo
                zip_ref.extractall(tmpdir)
                print(f"ZIP extraido em: {tmpdir}")
                
                # Lista o conteudo do diretorio apos extracao
                list_directory_contents(tmpdir)
                
                # Percorre o diretorio temporario procurando PDFs
                pdf_files = find_pdfs_in_dir(tmpdir)
                
        except zipfile.BadZipFile:
            print("ERRO: ZIP corrompido ou invalido!")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "ZIP corrompido ou invalido"})
            }
        except Exception as e:
            print(f"Erro ao extrair ZIP: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Erro ao extrair ZIP: {str(e)}"})
            }
        
        if not pdf_files:
            print("Nenhum PDF encontrado!")
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Nenhum PDF encontrado no ZIP"})
            }
        
        # Cria metadado no DynamoDB
        if not create_metadata(loan_id, len(pdf_files)):
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Falha ao criar metadado"})
            }
        
        # Upload dos PDFs para raw/ (DENTRO do bloco with)
        print("Iniciando upload dos PDFs...")
        for pdf in pdf_files:
            output_key = f"raw/{loan_id}/{pdf['base_name']}"
            print(f"Upload: {output_key} (de: {pdf['file_path']})")
            
            try:
                # Verifica se o arquivo existe antes do upload
                if not os.path.exists(pdf['file_path']):
                    print(f"Arquivo nao encontrado: {pdf['file_path']}")
                    continue
                    
                # Verifica o tamanho do arquivo
                file_size = os.path.getsize(pdf['file_path'])
                print(f"Tamanho do arquivo: {file_size} bytes")
                    
                s3.upload_file(
                    pdf["file_path"],
                    bucket,
                    output_key,
                    ExtraArgs={"ContentType": "application/pdf"}
                )
                uploaded.append(output_key)
                print(f"Upload concluído: {output_key}")
            except Exception as e:
                print(f"Erro ao fazer upload de {pdf['base_name']}: {e}")
                continue
    
    # O diretorio temporario é deletado aqui, mas os uploads ja foram feitos
    print(f"Total de uploads realizados: {len(uploaded)}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "ZIP processado com sucesso",
            "loan_id": loan_id,
            "total_pdfs": len(pdf_files),
            "uploaded": uploaded
        })
    }

def get_metadado(loan_id):
    """Busca metadado no DynamoDB"""
    try:
        response = table.get_item(Key={"loan_id": loan_id})
        return response.get("Item")
    except Exception as e:
        print(f"Erro ao buscar metadado: {e}")
        return None

def update_processing_status(loan_id, invocation_id, job_key):
    """Atualiza contador e marca job como DONE"""
    try:
        result = table.update_item(
            Key={"loan_id": loan_id},
            UpdateExpression="ADD processed_documents :inc",
            ExpressionAttributeValues={":inc": 1},
            ReturnValues="ALL_NEW"
        )
        
        table.update_item(
            Key={"loan_id": loan_id},
            UpdateExpression="SET bda_jobs.#job_key.#state = :done",
            ExpressionAttributeNames={
                "#job_key": job_key,
                "#state": "state"
            },
            ExpressionAttributeValues={":done": "DONE"}
        )
        
        return result["Attributes"]
    except Exception as e:
        print(f"Erro ao atualizar: {e}")
        raise

def check_completion(loan_id, metadado):
    """Verifica se todos os documentos foram processados"""
    bda_jobs = metadado.get("bda_jobs", {})
    ready = 0
    
    for job_key, job_info in bda_jobs.items():
        invocation_id = job_info.get("invocation_id")
        state = job_info.get("state")
        
        if state == "DONE":
            ready += 1
            continue
        
        key = f"bda-output/{loan_id}/{invocation_id}/0/custom_output/0/result.json"
        try:
            s3.head_object(Bucket=BUCKET, Key=key)
            ready += 1
        except:
            pass
    
    return ready, metadado.get("expected_documents", 0)

def publish_event(loan_id):
    """Dispara evento para o Lambda BDA"""
    try:
        events.put_events(Entries=[{
            "Source": "loan.upload",
            "DetailType": "LoanCreated",
            "EventBusName": "loan-idp-bus",
            "Detail": json.dumps({"loan_id": loan_id})
        }])
        print(f"Evento publicado para loan_id: {loan_id}")
    except Exception as e:
        print(f"Erro ao publicar evento: {e}")
        raise

def process_bda_result(event):
    """Processa resultado do BDA (arquivo JSON)"""
    print("=== PROCESSANDO RESULTADO BDA ===")
    
    try:
        key = event["Records"][0]["s3"]["object"]["key"]
        parts = key.split("/")
        loan_id = parts[1]
        invocation_id = parts[2]
        
        print(f"Processando: loan_id={loan_id}, invocation_id={invocation_id}")
        
        metadado = get_metadado(loan_id)
        if not metadado:
            return {"statusCode": 404, "body": json.dumps({"error": "Metadado não encontrado"})}
        
        bda_jobs = metadado.get("bda_jobs", {})
        job_key = None
        for key_job, value_job in bda_jobs.items():
            if value_job.get("invocation_id") == invocation_id:
                job_key = key_job
                break
        
        if not job_key:
            return {"statusCode": 404, "body": json.dumps({"error": f"Job não encontrado: {invocation_id}"})}
        
        updated = update_processing_status(loan_id, invocation_id, job_key)
        print(f"Processados: {updated.get('processed_documents', 0)}/{updated.get('expected_documents', 0)}")
        
        ready, expected = check_completion(loan_id, metadado)
        print(f"Prontos: {ready}/{expected}")
        
        if ready < expected:
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Aguardando", "ready": ready, "expected": expected})
            }
        
        print(f"Todos os {expected} documentos processados!")
        publish_event(loan_id)
        
        table.update_item(
            Key={"loan_id": loan_id},
            UpdateExpression="SET #s = :status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":status": "READY_TO_NORMALIZE"}
        )
        
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Processamento concluído", "loan_id": loan_id})
        }
        
    except Exception as e:
        print(f"ERRO: {e}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

def lambda_handler(event, context):
    print("EVENT RECEBIDO:", json.dumps(event))
    
    if "Records" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "Evento inválido"})}
    
    # Pega a chave do arquivo
    key = event["Records"][0]["s3"]["object"]["key"]
    bucket = event["Records"][0]["s3"]["bucket"]["name"]
    
    print(f"Key: {key}")
    print(f"Bucket: {bucket}")
    print(f"Termina com .zip? {key.endswith('.zip')}")
    
    # Verifica se é um arquivo ZIP
    if key.endswith(".zip"):
        # Extrai loan_id do caminho
        parts = key.split("/")
        if len(parts) >= 2:
            loan_id = parts[1]
            print(f"loan_id extraido: {loan_id}")
            return process_zip(bucket, key, loan_id)
        else:
            return {"statusCode": 400, "body": json.dumps({"error": "Caminho inválido para extrair loan_id"})}
    
    # Verifica se é resultado do BDA
    elif key.startswith("bda-output/") and key.endswith(".json"):
        return process_bda_result(event)
    
    # Qualquer outro arquivo
    else:
        print(f"Arquivo ignorado: {key}")
        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Arquivo ignorado", "key": key})
        }