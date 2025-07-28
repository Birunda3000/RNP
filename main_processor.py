import os
from config import config
from data_processor.processing import process_raw_file

if __name__ == "__main__":
    print("======================================================")
    print("=    INICIANDO SCRIPT DE PROCESSAMENTO DE DADOS      =")
    print("======================================================")

    # Itera sobre cada tipo de métrica configurada
    for metric_name, metric_info in config.METRIC_CONFIG.items():
        raw_metric_dir = os.path.join(config.RAW_DATA_PATH, metric_info['folder_name'])
        
        if not os.path.exists(raw_metric_dir):
            print(f"[ALERTA] Diretório de dados brutos não encontrado para '{metric_name}': {raw_metric_dir}")
            continue

        processed_metric_dir = os.path.join(config.PROCESSED_DATA_PATH, metric_info['folder_name'])
        csv_header = metric_info['csv_header']

        # Lista todos os arquivos JSON no diretório da métrica
        for filename in os.listdir(raw_metric_dir):
            if filename.endswith(".json"):
                raw_filepath = os.path.join(raw_metric_dir, filename)
                process_raw_file(raw_filepath, processed_metric_dir, metric_name, csv_header)

    print("\n======================================================")
    print("=         PROCESSAMENTO DE DADOS FINALIZADO          =")
    print("======================================================")