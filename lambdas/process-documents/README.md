# Lambda - Processamento de Documentos

## Objetivo

Esta função é responsável por processar os documentos PDF e transformar informações não estruturadas em dados estruturados que possam ser utilizados por aplicações de negócio usando a ferramenta AWS Bedrock data automation.

## Disparador

Evento gerado após a extração dos documentos PDF.

## Fluxo de Execução

1. Recebe os metadados do documento;
2. Recupera o arquivo armazenado no Amazon S3;
3. Envia o documento para processamento automatizado;
4. Interpreta a resposta do serviço de análise;
5. Prepara os dados estruturados para persistência.

## Entrada

Metadados do documento e localização do arquivo no Amazon S3.

## Saída

Informações estruturadas extraídas do documento.

## Serviços Utilizados

* AWS Lambda
* Amazon S3
* Amazon Bedrock Data Automation
* Amazon EventBridge
