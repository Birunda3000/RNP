import os
import time
import csv
from datetime import date, datetime
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# --- CONFIGURAÇÕES GERAIS ---
BASE_URL = "http://monipe-central.rnp.br"
ARCHIVE_URL = f"{BASE_URL}/esmond/perfsonar/archive/"
TIME_RANGE_SECONDS = "12628000"
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 15
CLIENT_RATE_LIMIT_DELAY = 5
OUTPUT_FOLDER = "datasets_arestas/" # <<< PASTA NOVA, não interfere com a antiga
disable_warnings(InsecureRequestWarning)


def make_api_request(url, params=None):
    """Função robusta para fazer requisições à API com retentativas."""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"   [INFO] Tentativa {attempt + 1}/{MAX_RETRIES} para o endereço: {url}")
            response = requests.get(url, params=params, verify=False, timeout=30)
            if response.status_code == 200:
                print("   [SUCESSO] Resposta recebida (Status 200).")
                return response.json()
            print(f"   [ALERTA] Status: {response.status_code}. Tentando novamente em {RETRY_DELAY_SECONDS}s...")
        except requests.exceptions.RequestException as e:
            print(f"   [ERRO] Falha na conexão: {e}")
        time.sleep(RETRY_DELAY_SECONDS)
    print(f"!!! [ERRO FATAL] Todas as {MAX_RETRIES} tentativas falharam para a URL: {url} !!!")
    return None


def create_output_folder_if_not_exists(folder_path):
    """Verifica se uma pasta existe e, se não, a cria."""
    if not os.path.exists(folder_path):
        print(f"[INFO] Criando pasta de saída: {folder_path}")
        os.makedirs(folder_path)


def collect_and_save_traceroute_edges(source_host, dest_host):
    """
    Orquestra a coleta de dados de traceroute para um par e salva como uma lista de arestas.
    """
    print(f"\n--- Coletando arestas de {source_host} -> {dest_host} ---")
    
    # 1. Busca os metadados para encontrar a URI dos dados brutos
    metadata_params = {"pscheduler-test-type": "trace", "source": source_host, "destination": dest_host}
    metadata = make_api_request(ARCHIVE_URL, params=metadata_params)
    if not metadata:
        print(f"!!! Não foi possível obter metadados. Pulando este par.")
        return

    # 2. Procura a URI correta nos metadados
    data_uri = next((et.get("base-uri") for obj in metadata for et in obj.get("event-types", []) if et.get("event-type") == "packet-trace"), None)
    if not data_uri:
        print(f"!!! Não foi encontrada a URI para 'packet-trace'. Pulando.")
        return

    # 3. Busca os dados brutos, que contêm tanto IP quanto Hostname
    data_url = f"{BASE_URL}{data_uri}"
    raw_traces = make_api_request(data_url, params={"time-range": TIME_RANGE_SECONDS})
    if not raw_traces:
        print(f"!!! Não foi possível obter os dados de rota. Pulando.")
        return

    # 4. Processa e salva os dados no novo formato de arestas
    create_output_folder_if_not_exists(OUTPUT_FOLDER)
    today_str = date.today().strftime('%Y-%m-%d')
    src_short = source_host.split('-')[1]
    dest_short = dest_host.split('-')[1]
    filename = f"arestas_{src_short}-{dest_short}_{today_str}.csv"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    total_edges = 0
    try:
        with open(filepath, "w", encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Datetime", "Hop_Number", "Source_IP", "Source_Hostname", "Dest_IP", "Dest_Hostname"])

            for trace in raw_traces:
                ts = trace.get('ts')
                dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                hops = trace.get('val', [])

                for i in range(len(hops) - 1):
                    source_node = hops[i]
                    dest_node = hops[i+1]
                    
                    writer.writerow([
                        ts,
                        dt_str,
                        i + 1,
                        source_node.get('ip', 'No-IP'),
                        source_node.get('hostname', 'No-Hostname'),
                        dest_node.get('ip', 'No-IP'),
                        dest_node.get('hostname', 'No-Hostname')
                    ])
                    total_edges += 1
        
        if total_edges > 0:
            print(f"$$$ Sucesso! {total_edges} arestas salvas em: {filepath} $$$")
        else:
            print("   [INFO] Nenhuma rota encontrada no período de tempo especificado.")

    except Exception as e:
        print(f"!!! [ERRO FATAL] Falha ao escrever o arquivo CSV '{filepath}': {e}")


# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    address_list = [
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

    print("==========================================================")
    print("= INICIANDO SCRIPT DE COLETA DE ARESTAS (TRACEROUTE) - RNP =")
    print("==========================================================")
    
    for source in address_list:
        for destination in address_list:
            if source == destination:
                continue
            
            collect_and_save_traceroute_edges(source, destination)
            print(f"[INFO] Pausa de {CLIENT_RATE_LIMIT_DELAY} segundos antes do próximo par.")
            time.sleep(CLIENT_RATE_LIMIT_DELAY)

    print("\n==========================================================")
    print("=              SCRIPT DE COLETA FINALIZADO               =")
    print("==========================================================")