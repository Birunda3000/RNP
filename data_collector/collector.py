import os
import json
from datetime import date
from config import config
from data_collector.api_client import make_api_request

def create_folder_if_not_exists(folder_path):
    """Verifica se uma pasta existe e, se não, a cria."""
    if not os.path.exists(folder_path):
        print(f"[INFO] Criando pasta: {folder_path}")
        os.makedirs(folder_path)

def fetch_and_save_raw_data(metric_name, source, destination):
    """
    Busca os dados brutos de uma métrica e salva o resultado em um arquivo JSON.
    Retorna uma tupla (status_boolean, mensagem).
    """
    metric_info = config.METRIC_CONFIG[metric_name]
    print(f"\n--- Coletando '{metric_name}' para {source} -> {destination} ---")

    # 1. Busca metadados
    metadata_params = {
        "pscheduler-test-type": metric_info['type'],
        "source": source,
        "destination": destination,
    }
    metadata = make_api_request(config.ARCHIVE_URL, params=metadata_params)
    if not metadata:
        reason = f"Metadados não encontrados para o par."
        print(f"!!! [ERRO] {reason} Pulando.")
        return (False, reason)

    # 2. Procura a URI
    base_uri = None
    for obj in metadata:
        for event_type in obj.get("event-types", []):
            if event_type.get("event-type") == metric_info['label']:
                base_uri = event_type.get("base-uri")
                break
        if base_uri: break

    if not base_uri:
        reason = f"URI para o evento '{metric_info['label']}' não encontrada nos metadados."
        print(f"!!! [ALERTA] {reason} Pulando.")
        return (False, reason)

    # 3. Busca os dados brutos
    data_url = f"{config.BASE_URL}{base_uri}"
    data_params = {"time-range": config.TIME_RANGE_SECONDS}
    raw_data = make_api_request(data_url, params=data_params)

    if not raw_data:
        reason = "A API não retornou dados brutos para os parâmetros fornecidos."
        print(f"!!! [ERRO] {reason} Pulando.")
        return (False, reason)

    # 4. Salva os dados brutos em um arquivo JSON
    output_dir = os.path.join(config.RAW_DATA_PATH, metric_info['folder_name'])
    create_folder_if_not_exists(output_dir)

    today_str = date.today().strftime('%Y-%m-%d')
    src_short = source.split('.')[0]
    dest_short = destination.split('.')[0]
    filename = f"{src_short}_to_{dest_short}_{today_str}.json"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding='utf-8') as f:
            json.dump(raw_data, f, indent=4)
        print(f"$$$ [SUCESSO] Dados brutos salvos em: {filepath} $$$")
        return (True, filepath)
    except Exception as e:
        reason = f"Falha ao escrever o arquivo JSON: {e}"
        print(f"!!! [ERRO FATAL] {reason} !!!")
        return (False, reason)