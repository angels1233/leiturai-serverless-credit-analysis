# Decisões Arquiteturais

## Por que uma arquitetura Serverless?

A solução foi construída utilizando serviços serverless para reduzir a necessidade de gerenciamento de infraestrutura e permitir escalabilidade automática de acordo com a demanda.

### Benefícios

* Menor complexidade operacional;
* Modelo de pagamento por uso;
* Escalabilidade automática;
* Maior velocidade de desenvolvimento.

---

## Por que utilizar o API Gateway?

O API Gateway fornece um ponto de entrada seguro e escalável para clientes que precisam enviar documentos para processamento.

### Benefícios

* Serviço totalmente gerenciado;
* Alta disponibilidade;
* Integração nativa com AWS Lambda;
* Redução do esforço operacional.

---

## Por que utilizar URLs Pré-Assinadas?

Arquivos de grande porte não devem trafegar diretamente pelo API Gateway ou pelo payload das funções Lambda.

### Benefícios

* Menor custo de processamento;
* Melhor desempenho;
* Upload direto para o Amazon S3;
* Controle de acesso temporário e seguro.

---

## Por que utilizar o EventBridge?

O EventBridge permite a construção de uma arquitetura orientada a eventos e reduz o acoplamento entre os componentes da solução.

### Benefícios

* Serviços desacoplados;
* Maior facilidade de manutenção;
* Melhor capacidade de evolução da solução;
* Integração nativa com serviços AWS.

---

## Por que utilizar AWS Lambda?

As funções Lambda executam a lógica de negócio somente quando necessário.

### Benefícios

* Ausência de gerenciamento de servidores;
* Escalabilidade automática;
* Redução de custos;
* Execução orientada a eventos.

---

## Por que utilizar o DynamoDB?

Os resultados do processamento são armazenados no DynamoDB devido à sua baixa latência e operação totalmente gerenciada.

### Benefícios

* Banco de dados serverless;
* Alta escalabilidade;
* Leituras e gravações de baixa latência;
* Baixo esforço operacional.

---

## Por que utilizar o CloudWatch?

O CloudWatch fornece monitoramento e observabilidade centralizados para todos os componentes da solução.

### Benefícios

* Centralização de logs;
* Métricas e monitoramento;
* Facilidade de troubleshooting;
* Maior visibilidade operacional.
