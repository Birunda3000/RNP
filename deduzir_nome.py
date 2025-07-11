import re
import os
from collections import Counter

# --- CONFIGURAÇÃO ---
ARQUIVO_DE_NOS = 'lista_completa_de_nos.txt'

def categorizar_nos():
    """
    Lê a lista de nós e os separa em dois grupos:
    1. Nós com exatamente um fragmento de nome que é uma sigla de estado.
    2. Todos os outros casos (nenhum match, múltiplos matches, ou padrões embutidos).
    """
    if not os.path.exists(ARQUIVO_DE_NOS):
        print(f"🚨 ERRO: Arquivo '{ARQUIVO_DE_NOS}' não foi encontrado.")
        return

    # Nosso "dicionário" de siglas válidas
    estados_br = {
        'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
        'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
        'sp', 'se', 'to'
    }

    matches_perfeitos_unicos = []
    casos_complexos = []

    print(f"--- Lendo e analisando o arquivo: {ARQUIVO_DE_NOS} ---")
    with open(ARQUIVO_DE_NOS, 'r', encoding='utf-8') as f:
        for hostname in f:
            hostname = hostname.strip()
            if not hostname:
                continue

            # Casos que já sabemos que são complexos e não precisam de análise
            if 'no-hostname' in hostname.lower() or 'gateway' in hostname.lower():
                casos_complexos.append(hostname)
                continue

            # Divide o hostname em partes usando múltiplos delimitadores: '-', '.', '_' e espaço
            partes = re.split(r'[-._\s]', hostname.lower())

            # Encontra todas as partes que são exatamente uma sigla de estado
            candidatos = [p for p in partes if p in estados_br]

            # Separa nos grupos com base na contagem de candidatos
            if len(candidatos) == 1:
                matches_perfeitos_unicos.append(hostname)
            else:
                # Se encontrou 0 ou mais de 1 candidato, é um caso complexo
                casos_complexos.append(hostname)

    # --- APRESENTAÇÃO DOS RESULTADOS ---
    print("\n=======================================================")
    print("=    GRUPO 1: NÓS COM MATCH PERFEITO E ÚNICO          =")
    print(f"=    (Total: {len(matches_perfeitos_unicos)} nós)                                  =")
    print("=======================================================")
    for host in sorted(matches_perfeitos_unicos):
        print(f"  -> {host}")

    print("\n=======================================================")
    print("=    GRUPO 2: CASOS COMPLEXOS OU SEM MATCH DIRETO     =")
    print(f"=    (Total: {len(casos_complexos)} nós)                                  =")
    print("=======================================================")
    for host in sorted(casos_complexos):
        print(f"  -> {host}")
    
    print("\nAnálise de categorização concluída.")


if __name__ == "__main__":
    categorizar_nos()