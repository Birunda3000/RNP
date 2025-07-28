Claro, aqui está uma proposta de `README.md` para o seu repositório, gerada a partir dos arquivos fornecidos.

-----

# Coletor e Processador de Dados de Rede (RNP)

Este projeto consiste em um conjunto de scripts Python para automatizar a coleta e o processamento de dados de métricas de rede a partir de uma API. O sistema é dividido em duas etapas principais:

1.  **Coleta**: Busca dados brutos da API para pares de hosts específicos e os salva em formato JSON.
2.  **Processamento**: Converte os dados brutos JSON em arquivos CSV estruturados para análise.

## Estrutura do Projeto

A estrutura de diretórios do projeto está organizada da seguinte forma:

```
RNP/
├── config
│   ├── __init__.py
│   └── config.py
├── data
│   ├── processed
│   └── raw
├── data_collector
│   ├── __init__.py
│   ├── api_client.py
│   ├── collector.py
│   └── report_generator.py
├── data_processor
│   ├── __init__.py
│   └── processing.py
├── main_collector.py
├── main_processor.py
├── .gitignore
└── requirements.txt
```

## Funcionalidades

  * **Coleta Automatizada**: Itera sobre uma lista configurável de hosts e métricas para buscar dados.
  * **Cliente de API Robusto**: Inclui um mecanismo de tentativas (retries) com delay para lidar com falhas de conexão.
  * **Processamento de Dados**: Transforma os dados brutos JSON em formato CSV limpo e pronto para análise.
  * **Geração de Relatórios**: Ao final da coleta, gera um relatório (`.txt`) com o resumo da execução, incluindo sucessos, falhas e a taxa de sucesso.
  * **Modularidade**: O código é organizado em módulos para coleta (`data_collector`) e processamento (`data_processor`), facilitando a manutenção e expansão.
  * **Configuração Centralizada**: Todas as configurações importantes (hosts, URLs de API, métricas) são gerenciadas no arquivo `config/config.py`.

## Pré-requisitos

  * Python 3.x

## Instalação

1.  Clone este repositório para a sua máquina local:

    ```bash
    git clone <URL_DO_SEU_REPOSITORIO>
    cd RNP
    ```

2.  Instale as dependências necessárias usando o `pip`:

    ```bash
    pip install -r requirements.txt
    ```

## Configuração

Antes de executar os scripts, é essencial configurar os parâmetros no arquivo `config/config.py`. As principais variáveis a serem ajustadas são:

  * `HOST_LIST`: A lista de hosts de origem e destino para a coleta de dados.
  * `METRIC_CONFIG`: Um dicionário que define as métricas a serem coletadas, seus tipos, labels na API e onde salvá-las.
  * `ARCHIVE_URL` e `BASE_URL`: As URLs base da API de onde os dados serão extraídos.
  * `MAX_RETRIES` e `RETRY_DELAY_SECONDS`: Parâmetros para o mecanismo de tentativas do cliente de API.

## Como Usar

A execução do projeto é dividida em duas etapas manuais.

### Etapa 1: Coletar os Dados Brutos

Execute o script principal de coleta. Ele buscará os dados para todos os pares de hosts e métricas configurados.

```bash
python main_collector.py
```

  * **O que ele faz**:
      * Para cada par de hosts e métrica, o script faz requisições à API.
      * Os dados brutos retornados são salvos em arquivos `.json` dentro de `data/raw/<nome_da_metrica>/`.
      * Ao final, um arquivo `relatorio_coleta_AAAA-MM-DD_HH-MM-SS.txt` é gerado na raiz do projeto com um resumo completo da operação.

### Etapa 2: Processar os Dados

Após a conclusão da coleta, execute o script de processamento para converter os arquivos JSON em CSV.

```bash
python main_processor.py
```

  * **O que ele faz**:
      * O script varre o diretório `data/raw/` em busca de arquivos `.json`.
      * Cada arquivo é lido, processado de acordo com sua métrica (atraso, traceroute, etc.) e reescrito como um arquivo `.csv`.
      * Os arquivos resultantes são salvos em `data/processed/<nome_da_metrica>/`, prontos para serem usados em ferramentas de análise ou bancos de dados.

## Detalhes dos Módulos

  * `main_collector.py`: Orquestra o processo de coleta de dados, iterando sobre hosts e métricas.
  * `main_processor.py`: Orquestra o processo de tratamento dos dados, lendo os arquivos brutos e acionando os parsers.
  * `data_collector/api_client.py`: Contém a função para fazer requisições HTTP à API, com lógica de retentativas e tratamento de erros básicos.
  * `data_collector/collector.py`: Gerencia a lógica de buscar metadados, encontrar a URI correta e salvar os dados brutos em JSON.
  * `data_collector/report_generator.py`: Classe `CollectionReport` responsável por acumular os resultados da coleta e gerar um relatório de texto.
  * `data_processor/processing.py`: Contém as funções de "parser" que sabem como interpretar o JSON de cada métrica e convertê-lo para um formato tabular (CSV).
