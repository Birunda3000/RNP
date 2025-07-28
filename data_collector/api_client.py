import time
import requests
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from config import config

# Desabilitar avisos de segurança
disable_warnings(InsecureRequestWarning)

def make_api_request(url, params=None):
    """
    Função centralizada para fazer requisições à API, com retries e tratamento de erro.
    """
    for attempt in range(config.MAX_RETRIES):
        try:
            print(f"   [INFO] Tentativa {attempt + 1}/{config.MAX_RETRIES} para: {url}")
            response = requests.get(
                url,
                params=params,
                verify=False,
                timeout=config.REQUEST_TIMEOUT_SECONDS
            )

            if response.status_code == 200:
                print("   [SUCESSO] Resposta recebida (Status 200).")
                return response.json()
            elif response.status_code == 404:
                print("   [ERRO] Recurso não encontrado (Status 404).")
                return None
            else:
                print(f"   [ALERTA] Status inesperado: {response.status_code}.")

        except requests.exceptions.RequestException as e:
            print(f"   [ERRO] Falha na conexão: {e}")

        if attempt < config.MAX_RETRIES - 1:
            print(f"   [ALERTA] Aguardando {config.RETRY_DELAY_SECONDS}s para nova tentativa...")
            time.sleep(config.RETRY_DELAY_SECONDS)

    print(f"!!! [ERRO FATAL] Todas as {config.MAX_RETRIES} tentativas falharam para a URL: {url} !!!")
    return None