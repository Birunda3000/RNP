import pandas as pd
import os

# --- CONFIGURAÇÃO ---
# Nome do arquivo CSV consolidado que será usado como entrada.
ARQUIVO_DE_ENTRADA = 'banco_de_dados_de_arestas.csv'

# Nome do arquivo de texto que será gerado com a lista de todos os nós únicos.
ARQUIVO_DE_SAIDA_TXT = 'lista_completa_de_nos.txt'


def extrair_e_salvar_nos_unicos(csv_path, txt_path):
    """
    Carrega o arquivo CSV consolidado, extrai todos os nomes de servidores
    (nós) únicos e os salva em um arquivo de texto (.txt).
    """
    # 1. Verifica se o arquivo de entrada existe
    if not os.path.exists(csv_path):
        print(f"🚨 ERRO: O arquivo de entrada '{csv_path}' não foi encontrado.")
        print("   Certifique-se de que o script 'consolidar_arestas.py' foi executado primeiro.")
        return

    try:
        print(f"--- Lendo o arquivo '{csv_path}' com Pandas ---")
        # 2. Carrega os dados para um DataFrame
        df = pd.read_csv(csv_path)

        # 3. Extrai e combina as colunas de hostname
        print("--- Identificando todos os servidores (nós) únicos ---")
        coluna_origem = df['Source_Hostname']
        coluna_destino = df['Dest_Hostname']
        
        # Junta as duas colunas em uma única lista gigante de nomes
        todos_os_nomes = pd.concat([coluna_origem, coluna_destino])
        
        # O método .unique() do Pandas remove todas as duplicatas.
        # Em seguida, convertemos para uma lista e ordenamos alfabeticamente.
        lista_de_nos_unicos = sorted(list(todos_os_nomes.unique()))

        # 4. Escreve a lista final no arquivo de texto
        print(f"--- Salvando {len(lista_de_nos_unicos)} nós únicos em '{txt_path}' ---")
        with open(txt_path, 'w', encoding='utf-8') as f:
            for nome_do_no in lista_de_nos_unicos:
                f.write(nome_do_no + '\n')
        
        print(f"\n$$$ SUCESSO! A lista de nós foi salva em '{txt_path}' $$$")

    except Exception as e:
        print(f"🚨 Ocorreu um erro inesperado durante o processamento: {e}")

# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    extrair_e_salvar_nos_unicos(ARQUIVO_DE_ENTRADA, ARQUIVO_DE_SAIDA_TXT)