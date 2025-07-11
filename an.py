import pandas as pd
import os

# --- CONFIGURAÇÃO ---
# Nome do arquivo CSV consolidado que será analisado.
# Certifique-se de que este arquivo foi gerado pelo script 'consolidar_arestas.py'
ARQUIVO_CONSOLIDADO = 'banco_de_dados_de_arestas.csv'

def analisar_dataframe(filepath):
    """
    Carrega o arquivo CSV consolidado em um DataFrame do Pandas e
    realiza uma análise básica.
    """
    # Verifica se o arquivo de entrada existe antes de tentar carregá-lo
    if not os.path.exists(filepath):
        print(f"🚨 ERRO: Arquivo '{filepath}' não encontrado.")
        print("   Por favor, execute o script de consolidação primeiro.")
        return

    print(f"--- Carregando o arquivo '{filepath}' para análise com Pandas ---")
    
    # Carrega o CSV para um DataFrame. Pandas cuida de todos os detalhes.
    df = pd.read_csv(filepath)
    
    print("✅ Arquivo carregado com sucesso!")
    print("-" * 50)

    # --- ANÁLISE DOS DADOS ---
    print("\n================ Análise Inicial do DataFrame ================")

    # 1. Contar o número total de linhas (arestas), como solicitado
    total_arestas = len(df)
    print(f"\n1. Número Total de Registros (Arestas): {total_arestas}")

    # 2. Análise extra: Contar o número de "viagens" únicas (baseado no Timestamp)
    viagens_unicas = df['Timestamp'].nunique()
    print(f"2. Número de 'Viagens' (Traceroutes) Únicas: {viagens_unicas}")

    # 3. Análise extra: Contar o número de nós únicos (baseado nos IPs)
    ips_origem = df['Source_IP']
    ips_destino = df['Dest_IP']
    total_ips_unicos = pd.concat([ips_origem, ips_destino]).nunique()
    print(f"3. Número de Nós (IPs) Únicos na Rede Mapeada: {total_ips_unicos}")

    # 4. Análise extra: Mostrar as 5 primeiras linhas para visualização
    print("\n4. Amostra dos Dados (5 primeiras linhas):")
    # Usamos to_string() para garantir que todas as colunas sejam exibidas
    print(df.head().to_string())
    
    print("\n====================== Fim da Análise ======================")


# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    analisar_dataframe(ARQUIVO_CONSOLIDADO)