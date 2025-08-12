import os
import time
from config import config
from data_collector.collector import fetch_and_save_raw_data
from data_collector.report_generator import CollectionReport # Importa a nova classe

if __name__ == "__main__":
    print("======================================================")
    print("=      INICIANDO SCRIPT DE COLETA DE DADOS - RNP     =")
    print("======================================================")

    # Inicializa o objeto de relatório
    report = CollectionReport()

    # Loop para iterar sobre todos os pares de origem e destino
    for source in config.HOST_LIST:
        for destination in config.HOST_LIST:
            if source == destination:
                continue

            # Para cada par, busca todas as métricas configuradas
            for metric_name in config.METRIC_CONFIG.keys():
                # Executa a coleta e captura o status e a mensagem
                success, message = fetch_and_save_raw_data(metric_name, source, destination)

                # Adiciona o resultado ao relatório
                if success:
                    report.add_success(metric_name, source, destination, message)
                else:
                    report.add_failure(metric_name, source, destination, message)

            # Pausa para não sobrecarregar o servidor
            print(f"\n[INFO] Pausa de {config.CLIENT_RATE_LIMIT_DELAY}s antes do próximo par.")
            time.sleep(config.CLIENT_RATE_LIMIT_DELAY)

    print("\n======================================================")
    print("=          COLETA DE DADOS BRUTOS FINALIZADA         =")
    print("======================================================")

    # Gera e salva o relatório de execução na pasta raiz do projeto (RNP/)
    report.save_report(config.BASE_DIR)