import pandas as pd
import os
import re
"""
Script para buscar viagens de traceroute por IP.
Ele lê o log de viagens gerado anteriormente e procura por todas as
jornadas que incluem o IP alvo ou qualquer um de seus nomes associados."""
# --- CONFIGURAÇÕES ---
PASTA_OUTPUT = 'output'
ARQUIVO_INPUT_NODES = os.path.join(PASTA_OUTPUT, 'nodes.csv')
ARQUIVO_INPUT_JORNADAS = os.path.join(PASTA_OUTPUT, 'traceroute_journeys.csv')
# Novo nome de arquivo para o resultado da pesquisa
ARQUIVO_SAIDA_PESQUISA = os.path.join(PASTA_OUTPUT, 'pesquisa.csv')

def buscar_e_salvar_viagens(target_ip: str):
    """
    Busca por um IP (ou seus nomes associados) no log de viagens e salva
    as jornadas únicas encontradas em um novo arquivo CSV.
    """
    print("--- INICIANDO SCRIPT: BUSCAR E SALVAR VIAGENS POR IP ---")

    # Etapa 1: Carregar os dados necessários
    print("🔎 Carregando arquivos de nós e jornadas...")
    try:
        df_nodes = pd.read_csv(ARQUIVO_INPUT_NODES)
        df_journeys = pd.read_csv(ARQUIVO_INPUT_JORNADAS)
    except FileNotFoundError as e:
        print(f"🚨 ERRO: Arquivo não encontrado - {e.filename}")
        print("   -> Certifique-se de que os scripts anteriores foram executados com sucesso.")
        return
    print("✅ Arquivos carregados.")

    # Etapa 2: Encontrar todos os nomes associados ao IP alvo
    node_info = df_nodes[df_nodes['ip'] == target_ip]
    termos_de_busca = {target_ip}
    if not node_info.empty:
        nomes_str = node_info['nome'].iloc[0]
        if nomes_str and pd.notna(nomes_str):
            termos_de_busca.update(nomes_str.split(';'))
    
    print(f"\n🔍 Buscando por qualquer um destes termos: {list(termos_de_busca)}")

    # Etapa 3: Filtrar as viagens que contêm qualquer um dos termos de busca
    regex_pattern = "|".join([re.escape(term) for term in termos_de_busca if term])
    viagens_encontradas = df_journeys[df_journeys['sequencia_saltos'].str.contains(regex_pattern, na=False, regex=True)]

    if viagens_encontradas.empty:
        print(f"\n✅ Nenhuma viagem encontrada para o IP '{target_ip}' ou seus nomes associados.")
        print(f"   -> O arquivo '{ARQUIVO_SAIDA_PESQUISA}' não será modificado ou criado.")
        return

    # Etapa 4: Remover duplicatas
    viagens_unicas = viagens_encontradas.drop_duplicates(subset=['sequencia_saltos']).copy()

    # --- MUDANÇA NA LÓGICA: SALVAR EM VEZ DE EXIBIR ---
    print(f"\n--- 💾 Salvando {len(viagens_unicas)} VIAGENS ÚNICAS em '{ARQUIVO_SAIDA_PESQUISA}' ---")

    # Seleciona as colunas mais relevantes para o arquivo de saída
    colunas_para_salvar = [
        'id', 
        'timestamp', 
        'estado_origem', 
        'estado_destino', 
        'sequencia_saltos',
        'nome_arquivo_origem'
    ]
    
    resultado_final = viagens_unicas[colunas_para_salvar]

    try:
        resultado_final.to_csv(ARQUIVO_SAIDA_PESQUISA, index=False, encoding='utf-8')
        print(f"✅ Arquivo salvo com sucesso.")
    except Exception as e:
        print(f"🚨 ERRO ao salvar o arquivo: {e}")
    
    print("\n--- Fim do Script ---")


if __name__ == '__main__':
    # --- PONTO DE INTERESSE ---
    # Altere o valor desta variável para buscar o IP que você deseja investigar.
    #ip_alvo = "200.237.194.2"
    ip_alvo = "170.79.213.123" 

    if not ip_alvo:
        print("🚨 Por favor, defina um valor para a variável 'ip_alvo' no script.")
    else:
        buscar_e_salvar_viagens(ip_alvo)