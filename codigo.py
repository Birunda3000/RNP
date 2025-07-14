import os
import time
from datetime import date, datetime
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# --- CONFIGURAÇÕES GERAIS ---
# Todas as configurações importantes estão aqui para fácil modificação.

# URL base da API do Esmond/perfSONAR da RNP
BASE_URL = "http://monipe-central.rnp.br"
ARCHIVE_URL = f"{BASE_URL}/esmond/perfsonar/archive/"

# Configurações para as tentativas de requisição (retry)
MAX_RETRIES = 20  # Número máximo de vezes que o script tentará uma requisição antes de desistir.
RETRY_DELAY_SECONDS = 60  # Tempo de espera (em segundos) entre as tentativas.

# Configuração do período de tempo para a coleta de dados (em segundos)
# O valor original era "63072000" (2 anos), que é muito grande e pode causar erros.
# Recomendo usar períodos menores, como 1 mês (aprox. 2.628.000 segundos)
TIME_RANGE_SECONDS = "12628000"  # Exemplo: 1 mês

# Configuração de pausa para não sobrecarregar o servidor
# Pausa (em segundos) entre as requisições para cada par de hosts (origem/destino).
CLIENT_RATE_LIMIT_DELAY = 3

# Desabilitar avisos de segurança para requisições HTTPS não verificadas (como no original)
disable_warnings(InsecureRequestWarning)

# --- FUNÇÕES AUXILIARES ---

def make_api_request(url, params=None):
    """
    Função centralizada e robusta para fazer requisições à API.
    Ela gerencia as tentativas (retries), timeouts e trata diferentes códigos de erro.
    """
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   [INFO] Tentativa {attempt + 1}/{MAX_RETRIES} para o endereço: {url}")
            response = requests.get(url, params=params, verify=False, timeout=30)  # Timeout de 30s

            if response.status_code == 200:
                print(f"   [SUCESSO] Resposta recebida com sucesso (Status 200).")
                return response.json()
            
            # Trata erros específicos para dar mensagens mais claras
            elif response.status_code == 429:
                print(f"   [ALERTA] Servidor respondeu com '429 Too Many Requests'. Fomos bloqueados temporariamente.")
            elif response.status_code == 503:
                print(f"   [ALERTA] Servidor respondeu com '503 Service Unavailable'. Pode estar sobrecarregado.")
            elif response.status_code == 404:
                print(f"   [ERRO] Servidor respondeu com '404 Not Found'. O recurso não existe.")
                return None # Não adianta tentar de novo se não existe
            else:
                print(f"   [ERRO] Recebido Status Code inesperado: {response.status_code}.")

        except requests.exceptions.RequestException as e:
            print(f"   [ERRO] Ocorreu um erro de conexão: {e}")

        # Se a requisição falhou, espera antes de tentar novamente
        if attempt < MAX_RETRIES - 1:
            print(f"   [ALERTA] Aguardando {RETRY_DELAY_SECONDS} segundos antes da próxima tentativa...")
            time.sleep(RETRY_DELAY_SECONDS)

    print(f"!!! [ERRO FATAL] Todas as {MAX_RETRIES} tentativas falharam para a URL: {url} !!!")
    return None


def create_output_folder_if_not_exists(folder_path):
    """Verifica se uma pasta existe e, se não, a cria."""
    if not os.path.exists(folder_path):
        print(f"[INFO] Criando pasta de saída em: {folder_path}")
        os.makedirs(folder_path)


def calc_mean(values):
    """Calcula a média de uma lista de valores numéricos."""
    if not values:
        return 0.0
    numeric_values = [float(v) for v in values]
    return round(sum(numeric_values) / len(numeric_values), 2)


# --- FUNÇÕES DE PARSING DE DADOS ---
# Cada função é especializada em extrair e formatar os dados de um tipo de métrica.

def parse_atraso_data(raw_data):
    """Parser para os dados de atraso (histogram-owdelay)."""
    for item in raw_data:
        timestamp = int(item.get('ts', 0))
        datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        # O valor de atraso é uma lista de medições, calculamos a média
        mean_delay = calc_mean(item.get('val', []))
        yield f"{timestamp},{datetime_str},{mean_delay}\n"


def parse_traceroute_data(raw_data):
    """Parser para os dados de traceroute (packet-trace)."""
    for item in raw_data:
        timestamp = int(item.get('ts', 0))
        datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        hops = item.get('val', [])
        # Extrai o hostname de cada salto (hop) no traceroute
        hostnames = [hop.get('hostname', 'No-Hostname') for hop in hops]
        yield f"{timestamp},{datetime_str},{';'.join(hostnames)}\n"


def parse_loss_data(raw_data):
    """Parser para os dados de perda de pacotes (packet-loss-rate-bidir)."""
    for item in raw_data:
        timestamp = int(item.get('ts', 0))
        datetime_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        loss_value = item.get('val')
        # O valor pode ser único ou uma lista, o código original trata ambos
        if isinstance(loss_value, list):
            for v in loss_value:
                yield f"{timestamp},{datetime_str},{v}\n"
        else:
            yield f"{timestamp},{datetime_str},{loss_value}\n"


# --- FUNÇÃO PRINCIPAL DE COLETA ---

def fetch_and_save_data(metric_config, source, destination):
    """
    Função genérica que busca os metadados de uma métrica, encontra a URI dos dados
    e chama o parser apropriado para processar e salvar os resultados em um CSV.
    """
    metric_name = metric_config['name']
    print(f"\n--- Iniciando coleta de '{metric_name}' para {source} -> {destination} ---")
    
    # 1. Busca os metadados para encontrar o link dos dados brutos
    metadata_params = {
        "pscheduler-test-type": metric_config['type'],
        "source": source,
        "destination": destination,
    }
    metadata = make_api_request(ARCHIVE_URL, params=metadata_params)

    if not metadata:
        print(f"!!! [ERRO FATAL] Não foi possível obter os metadados para '{metric_name}'. Pulando este par. !!!")
        return

    # 2. Procura a URI correta nos metadados
    base_uri = None
    for obj in metadata:
        for event_type in obj.get("event-types", []):
            if event_type.get("event-type") == metric_config['label']:
                base_uri = event_type.get("base-uri")
                break
        if base_uri:
            break
            
    if not base_uri:
        print(f"!!! [ALERTA] Não foi encontrada a URI para o tipo de evento '{metric_config['label']}' para '{metric_name}'. Pulando. !!!")
        return

    # 3. Busca os dados brutos usando a URI encontrada
    data_url = f"{BASE_URL}{base_uri}"
    data_params = {"time-range": TIME_RANGE_SECONDS}
    raw_data = make_api_request(data_url, params=data_params)

    if not raw_data:
        print(f"!!! [ERRO FATAL] Não foi possível obter os dados brutos de '{metric_name}'. Pulando este par. !!!")
        return

    # 4. Processa e salva os dados em um arquivo CSV
    folder = metric_config['folder']
    create_output_folder_if_not_exists(folder)
    
    today_str = date.today().strftime('%m-%d-%Y')
    src_short = source.split('-')[1]
    dest_short = destination.split('-')[1]
    filename = f"{metric_name} esmond data {src_short}-{dest_short} {today_str}.csv"
    filepath = os.path.join(folder, filename)

    try:
        with open(filepath, "w", encoding='utf-8') as f:
            f.write(metric_config['header'] + "\n")
            
            count = 0
            # Usa o parser específico para formatar cada linha
            parser_func = metric_config['parser']
            for line in parser_func(raw_data):
                f.write(line)
                count += 1
        
        print(f"$$$ [SUCESSO TOTAL] Dados de '{metric_name}' salvos com sucesso! $$$")
        print(f"   -> Arquivo: {filepath}")
        print(f"   -> Total de {count} registros salvos.")

    except Exception as e:
        print(f"!!! [ERRO FATAL] Ocorreu um erro ao escrever o arquivo CSV '{filepath}': {e} !!!")


# --- BLOCO DE EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":
    # Listas de hosts (origem/destino) como no original
    address_atraso = [
        "monipe-ce-atraso.rnp.br", "monipe-ac-atraso.rnp.br", "monipe-am-atraso.rnp.br",
        "monipe-ap-atraso.rnp.br", "monipe-ba-atraso.rnp.br", "monipe-df-atraso.rnp.br",
        "monipe-es-atraso.rnp.br", "monipe-go-atraso.rnp.br", "monipe-ma-atraso.rnp.br",
        "monipe-mg-atraso.rnp.br", "monipe-ms-atraso.rnp.br", "monipe-mt-atraso.rnp.br",
        "monipe-pa-atraso.rnp.br", "monipe-pb-atraso.rnp.br", "monipe-pe-atraso.rnp.br",
        "monipe-pi-atraso.rnp.br", "monipe-pr-atraso.rnp.br", "monipe-rj-atraso.rnp.br",
        "monipe-rn-atraso.rnp.br", "monipe-ro-atraso.rnp.br", "monipe-rr-atraso.rnp.br",
        "monipe-rs-atraso.rnp.br", "monipe-sc-atraso.rnp.br", "monipe-se-atraso.rnp.br",
        "monipe-sp-atraso.rnp.br", "monipe-to-atraso.rnp.br"
    ]
    
    # Configuração de cada métrica a ser coletada
    METRICS_TO_FETCH = [
        {
            "name": "atraso",
            "folder": "datasets atraso/",
            "type": "latencybg",
            "label": "histogram-owdelay",
            "header": "Timestamp,Data,Atraso(ms)",
            "parser": parse_atraso_data
        },
        {
            "name": "traceroute",
            "folder": "datasets traceroute/",
            "type": "trace",
            "label": "packet-trace",
            "header": "Timestamp,Datetime,HopHostnames",
            "parser": parse_traceroute_data
        },
        {
            "name": "loss_bidir",
            "folder": "datasets perda/",
            "type": "rtt", # O tipo de teste que contém a perda bidirecional
            "label": "packet-loss-rate-bidir",
            "header": "Timestamp,Data,Loss",
            "parser": parse_loss_data
        }
    ]

    print("======================================================")
    print("=      INICIANDO SCRIPT DE COLETA DE DADOS - RNP     =")
    print(f"=      Data de Execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}      =")
    print("======================================================")

    # Loop principal para iterar sobre todos os pares de origem e destino
    for source in address_atraso:
        for destination in address_atraso:
            if source == destination:
                continue

            # Para rodar para todos, remova ou ajuste a condição abaixo
            # if destination.split("-")[1] in ["rs"]:
            
            # Para cada par, busca todas as métricas configuradas
            for metric in METRICS_TO_FETCH:
                fetch_and_save_data(metric, source, destination)

            # Pausa para não sobrecarregar o servidor
            print(f"\n[INFO] Pausa de {CLIENT_RATE_LIMIT_DELAY} segundos antes do próximo par de hosts.")
            time.sleep(CLIENT_RATE_LIMIT_DELAY)

    print("\n======================================================")
    print("=          SCRIPT DE COLETA FINALIZADO             =")
    print("======================================================")