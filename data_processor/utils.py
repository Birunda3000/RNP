# /utils.py
import os

def create_folder_if_not_exists(folder_path):
    """
    Verifica se uma pasta existe e, se não, a cria.
    """
    if not os.path.exists(folder_path):
        print(f"[INFO] Criando pasta: {folder_path}")
        os.makedirs(folder_path)

def get_state_from_filename(filename):
    """
    Extrai as siglas dos estados de origem e destino a partir do nome do arquivo.
    Exemplo: 'monipe-ac-atraso_to_monipe-am-atraso_2025-08-12.json' -> ('ac', 'am')
    """
    try:
        parts = os.path.basename(filename).split('_to_')
        source_part = parts[0]
        dest_part = parts[1]

        source_state = source_part.split('-')[1]
        dest_state = dest_part.split('-')[1]

        return source_state.upper(), dest_state.upper()
    except IndexError:
        print(f"[AVISO] Não foi possível extrair os estados do nome de arquivo: {filename}")
        return None, None