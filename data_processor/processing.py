import os
import json
from datetime import datetime

def create_folder_if_not_exists(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

def _calc_mean(values):
    if not values: return 0.0
    return round(sum(float(v) for v in values) / len(values), 2)

# --- Funções de Parser ---

def _parse_atraso(raw_data):
    for item in raw_data:
        ts = int(item.get('ts', 0))
        dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        mean_delay = _calc_mean(item.get('val', []))
        yield f"{ts},{dt_str},{mean_delay}\n"

def _parse_traceroute(raw_data):
    for item in raw_data:
        ts = int(item.get('ts', 0))
        dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        hostnames = [hop.get('hostname', 'N/A') for hop in item.get('val', [])]
        yield f"{ts},{dt_str},{';'.join(hostnames)}\n"

def _parse_loss_bidir(raw_data):
    for item in raw_data:
        ts = int(item.get('ts', 0))
        dt_str = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        loss = item.get('val')
        if isinstance(loss, list):
            for v in loss: yield f"{ts},{dt_str},{v}\n"
        else:
            yield f"{ts},{dt_str},{loss}\n"

# Mapeia o nome da métrica para sua função de parser
PARSERS = {
    "atraso": _parse_atraso,
    "traceroute": _parse_traceroute,
    "loss_bidir": _parse_loss_bidir,
}

def process_raw_file(raw_filepath, processed_dir, metric_name, metric_header):
    """
    Lê um arquivo JSON bruto, aplica o parser correto e salva como CSV.
    """
    parser_func = PARSERS.get(metric_name)
    if not parser_func:
        print(f"[ERRO] Parser para a métrica '{metric_name}' não encontrado.")
        return

    print(f"\n--- Processando arquivo: {os.path.basename(raw_filepath)} ---")
    try:
        with open(raw_filepath, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        if not raw_data:
            print("[ALERTA] Arquivo de dados brutos está vazio. Pulando.")
            return

        create_folder_if_not_exists(processed_dir)
        
        # Cria o nome do arquivo de saída .csv
        csv_filename = os.path.basename(raw_filepath).replace('.json', '.csv')
        csv_filepath = os.path.join(processed_dir, csv_filename)

        with open(csv_filepath, 'w', encoding='utf-8') as f:
            f.write(metric_header + "\n")
            count = 0
            for line in parser_func(raw_data):
                f.write(line)
                count += 1
        
        print(f"$$$ [SUCESSO] Dados processados salvos em: {csv_filepath}")
        print(f"    -> Total de {count} registros.")

    except json.JSONDecodeError:
        print(f"!!! [ERRO FATAL] Arquivo JSON inválido: {raw_filepath} !!!")
    except Exception as e:
        print(f"!!! [ERRO FATAL] Falha ao processar '{raw_filepath}': {e} !!!")