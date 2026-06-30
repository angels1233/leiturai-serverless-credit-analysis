# Lambda - Extração de Arquivos ZIP

## Objetivo

Esta função é responsável por receber notificações de novos arquivos enviados ao Amazon S3, descompactar os arquivos ZIP recebidos e disponibilizar os documentos PDF para as próximas etapas do processamento.

## Disparador

Evento do Amazon EventBridge após o upload do arquivo no Amazon S3.

## Fluxo de Execução

1. Recebe informações sobre o arquivo enviado;
2. Faz o download do arquivo ZIP armazenado no S3;
3. Extrai os documentos PDF;
4. Envia os arquivos extraídos para o bucket de processamento;
5. Disponibiliza os documentos para a próxima etapa do fluxo.

## Entrada

Evento contendo informações do objeto armazenado no S3.

## Saída

Documentos PDF extraídos e armazenados no bucket de processamento.

## Serviços Utilizados

* AWS Lambda
* Amazon S3
* Amazon EventBridge
