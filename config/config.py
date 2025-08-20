import os

# --- PATHS ---
# Caminhos para as pastas de dados
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed")

# --- API ---
# URL base da API do Esmond/perfSONAR da RNP
BASE_URL = "http://monipe-central.rnp.br"
ARCHIVE_URL = f"{BASE_URL}/esmond/perfsonar/archive/"

# --- REQUESTS ---
# Configurações para as tentativas de requisição (retry)
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
CLIENT_RATE_LIMIT_DELAY = 2 # Pausa entre pares de hosts
REQUEST_TIMEOUT_SECONDS = 5 # Timeout para cada requisição

# --- DATA COLLECTION ---
# Período de tempo para a coleta de dados (em segundos)
#"2628000"  # Exemplo: 1 mês
#"604800"  # Exemplo: 1 semana
TIME_RANGE_SECONDS = "2628000"

# --- HOSTS ---
HOST_LIST = [
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

# --- METRICS ---
# Dicionário com a configuração de cada métrica a ser coletada e processada.
METRIC_CONFIG = {
    "atraso": {
        "folder_name": "atraso",
        "type": "latencybg",
        "label": "histogram-owdelay",
        "csv_header": "Timestamp,Data,Atraso(ms)"
    },
    "traceroute": {
        "folder_name": "traceroute",
        "type": "trace",
        "label": "packet-trace",
        "csv_header": "Timestamp,Datetime,HopHostnames"
    },
    "loss_bidir": {
        "folder_name": "perda_bidirecional",
        "type": "rtt",
        "label": "packet-loss-rate-bidir",
        "csv_header": "Timestamp,Data,Loss"
    }
}