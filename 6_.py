import pandas as pd
import os
import re

# --- CONFIGURAÇÕES ---
PASTA_OUTPUT = 'output'
ARQUIVO_INPUT_NODES = os.path.join(PASTA_OUTPUT, 'nodes.csv')
ARQUIVO_INPUT_JORNADAS = os.path.join(PASTA_OUTPUT, 'traceroute_journeys.csv')
ARQUIVO_SAIDA_CSV = os.path.join(PASTA_OUTPUT, 'endpoint_journeys.csv')

def buscar_viagens_por_endpoint(target_ip: str):
    """
    Encontra todas as jornadas onde o IP fornecido (ou seus nomes associados)
    foi o primeiro ou o último salto da sequência.
    """
    print("--- INICIANDO SCRIPT: BUSCA DE VIAGENS POR NÓ DE EXTREMIDADE (ENDPOINT) ---")

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
    
    print(f"\n🔍 Buscando por nós de extremidade correspondentes a: {list(termos_de_busca)}")

    # Etapa 3: Identificar o primeiro e o último salto de cada jornada
    # Removemos linhas onde a sequência de saltos possa estar vazia para evitar erros
    df_journeys.dropna(subset=['sequencia_saltos'], inplace=True)
    
    # Divide a string de sequência em uma lista de saltos
    path_split = df_journeys['sequencia_saltos'].str.split(' -> ', expand=False)
    
    # Cria colunas temporárias com o primeiro e último salto já limpos (sem o '*')
    df_journeys['primeiro_salto'] = path_split.str[0].str.rstrip('*')
    df_journeys['ultimo_salto'] = path_split.str[-1].str.rstrip('*')
    
    # Etapa 4: Filtrar as jornadas onde o primeiro OU o último salto está na nossa lista de busca
    filtro_inicio = df_journeys['primeiro_salto'].isin(termos_de_busca)
    filtro_fim = df_journeys['ultimo_salto'].isin(termos_de_busca)
    
    # O operador '|' significa OU
    viagens_endpoint = df_journeys[filtro_inicio | filtro_fim].copy()

    # Remove as colunas temporárias que não são necessárias no arquivo final
    viagens_endpoint.drop(columns=['primeiro_salto', 'ultimo_salto'], inplace=True)

    if viagens_endpoint.empty:
        print(f"\n✅ Nenhuma viagem encontrada onde '{target_ip}' (ou seus nomes) é um nó de extremidade.")
        return

    # Etapa 5: Salvar o resultado
    print(f"\n--- 💾 Salvando {len(viagens_endpoint)} jornadas encontradas em '{ARQUIVO_SAIDA_CSV}' ---")
    
    try:
        viagens_endpoint.to_csv(ARQUIVO_SAIDA_CSV, index=False, encoding='utf-8')
        print(f"✅ Arquivo salvo com sucesso.")
    except Exception as e:
        print(f"🚨 ERRO ao salvar o arquivo: {e}")
        
    print("\n--- Fim do Script ---")

if __name__ == '__main__':
    # --- PONTO DE INTERESSE ---
    # Altere o valor desta variável para buscar o IP que você deseja investigar.
    ip_alvo = "170.79.213.123" # Ex: monipe-am-atraso.rnp.br
    
    if not ip_alvo:
        print("🚨 Por favor, defina um valor para a variável 'ip_alvo' no script.")
    else:
        buscar_viagens_por_endpoint(ip_alvo)