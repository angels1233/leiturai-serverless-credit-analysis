# Lambda - Geração de URL Pré-Assinada

## Objetivo

Esta função é responsável por gerar uma URL pré-assinada do Amazon S3, permitindo que clientes realizem o upload de arquivos ZIP de forma segura e direta no bucket de armazenamento e cria a tabela de metadado no DynamoDB

## Disparador

Amazon API Gateway.

## Fluxo de Execução

1. Recebe uma solicitação de upload;
2. Gera um identificador único para o arquivo;
3. Cria uma URL pré-assinada temporária;
4. Retorna as informações necessárias para o cliente realizar o upload.

## Entrada

Requisição HTTP enviada pelo cliente.

## Saída

* Identificador do upload;
* URL pré-assinada para envio do arquivo.

## Serviços Utilizados

* AWS Lambda
* Amazon API Gateway
* Amazon S3
