import os
import re
import json
import pandas as pd
from collections import Counter

# --- CONFIGURAÇÃO ---
ARQUIVO_NOS_ENTRADA = 'nodes.csv'
ARQUIVO_ARESTAS_ENTRADA = 'edges.csv'
PASTA_RAW_TRACEROUTE = os.path.join('data', 'raw', 'traceroute')

ARQUIVO_NOS_SAIDA = 'nodes_com_estados.csv'
ARQUIVO_RELATORIO_SAIDA = 'relatorio_de_deducao.txt'

ESTADOS_BR = {
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
    'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
    'sp', 'se', 'to'
}

# --- FUNÇÕES AUXILIARES DE DEDUÇÃO ---

def _deduzir_por_match_perfeito(hostname):
    """Aplica a Regra 2: Análise de Hostname (Match Perfeito)."""
    if not isinstance(hostname, str):
        return None
    
    partes = re.split(r'[-._\s]', hostname.lower())
    candidatos = [p for p in partes if p in ESTADOS_BR]

    if len(candidatos) > 0 and len(set(candidatos)) == 1:
        return candidatos[0].upper()
    return None

def _atualizar_estado_no(df, node_id, estado, metodo, confianca):
    """Função centralizada para atualizar o estado de um nó, respeitando a precedência."""
    # Só atualiza se o nó ainda não tiver um estado definido
    if pd.isna(df.loc[node_id, 'estado_deduzido']):
        df.loc[node_id, 'estado_deduzido'] = estado
        df.loc[node_id, 'metodo_deducao'] = metodo
        df.loc[node_id, 'nivel_confianca'] = confianca
        return True
    return False

# --- ETAPAS DO PIPELINE ---

def etapa_1_ancoras_de_viagem(df_nodes):
    """Aplica a Regra 1: Usa o início e fim de cada traceroute como âncoras."""
    print("--- Etapa 1: Aplicando Regra de Âncoras de Viagem (Confiança Nível 5) ---")
    updates = 0
    
    # Mapeamento de nome/ip para id para acesso rápido
    nome_ip_para_id = pd.Series(df_nodes.index, index=df_nodes['nome']).to_dict()
    nome_ip_para_id.update(pd.Series(df_nodes.index, index=df_nodes['ip']).to_dict())

    for filename in os.listdir(PASTA_RAW_TRACEROUTE):
        if not filename.endswith('.json'):
            continue
        
        # Extrai estados do nome do arquivo, ex: monipe-ac-atraso_to_monipe-ro-atraso...
        match = re.search(r'monipe-([a-z]{2})-atraso_to_monipe-([a-z]{2})-atraso', filename)
        if not match:
            continue
        estado_origem, estado_destino = match.groups()

        filepath = os.path.join(PASTA_RAW_TRACEROUTE, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                traces = json.load(f)
            except json.JSONDecodeError:
                continue
        
        for trace in traces:
            hops = trace.get('val', [])
            if len(hops) < 2:
                continue

            # Âncora de Origem (Primeiro Salto)
            primeiro_hop_id = hops[0].get('hostname') or hops[0].get('ip')
            if primeiro_hop_id in nome_ip_para_id:
                node_id = nome_ip_para_id[primeiro_hop_id]
                if _atualizar_estado_no(df_nodes, node_id, estado_origem.upper(), 'POP de Origem da Viagem', 5):
                    updates += 1

            # Âncora de Destino (Último Salto)
            ultimo_hop_id = hops[-1].get('hostname') or hops[-1].get('ip')
            if ultimo_hop_id in nome_ip_para_id:
                node_id = nome_ip_para_id[ultimo_hop_id]
                if _atualizar_estado_no(df_nodes, node_id, estado_destino.upper(), 'POP de Destino da Viagem', 5):
                    updates += 1

    print(f"✅ Etapa 1 concluída. {updates} nós definidos como âncoras.")
    return df_nodes

def etapa_2_match_perfeito(df_nodes):
    """Aplica a Regra 2: Análise de Hostname."""
    print("--- Etapa 2: Aplicando Regra de Match Perfeito no Hostname (Confiança Nível 4) ---")
    updates = 0
    # Itera apenas nos nós que ainda não têm estado e possuem um nome
    nodes_para_verificar = df_nodes[(df_nodes['estado_deduzido'].isna()) & (df_nodes['nome'] != '')]
    
    for node_id, row in nodes_para_verificar.iterrows():
        estado = _deduzir_por_match_perfeito(row['nome'])
        if estado:
            if _atualizar_estado_no(df_nodes, node_id, estado, 'Análise de Hostname (Match Perfeito)', 4):
                updates += 1

    print(f"✅ Etapa 2 concluída. {updates} nós definidos por match de hostname.")
    return df_nodes

def etapa_3_regra_sanduiche(df_nodes, df_edges):
    """Aplica a Regra 4: Um nó entre dois nós de um mesmo estado, também está nesse estado."""
    print("--- Etapa 3: Aplicando Regra do Sanduíche (Confiança Nível 3) ---")
    
    # Cria uma lista de adjacência para performance
    adj = {node_id: [] for node_id in df_nodes.index}
    for _, edge in df_edges.iterrows():
        adj[edge['source']].append(edge['target'])
        adj[edge['target']].append(edge['source'])

    total_updates = 0
    while True:
        updates_nesta_iteracao = 0
        nodes_sem_estado_ids = df_nodes[df_nodes['estado_deduzido'].isna()].index

        if len(nodes_sem_estado_ids) == 0:
            break

        for node_id in nodes_sem_estado_ids:
            vizinhos = adj.get(node_id, [])
            estados_dos_vizinhos = df_nodes.loc[vizinhos, 'estado_deduzido'].dropna()

            if len(estados_dos_vizinhos) > 1 and len(estados_dos_vizinhos.unique()) == 1:
                estado_deduzido = estados_dos_vizinhos.iloc[0]
                if _atualizar_estado_no(df_nodes, node_id, estado_deduzido, 'Inferência por Vizinhança (Sanduíche)', 3):
                    updates_nesta_iteracao += 1
        
        if updates_nesta_iteracao == 0:
            break # Loop estabilizou, não há mais o que deduzir com esta regra
        total_updates += updates_nesta_iteracao
        print(f"  -> Iteração da Regra do Sanduíche encontrou {updates_nesta_iteracao} novos estados...")

    print(f"✅ Etapa 3 concluída. {total_updates} nós definidos por inferência de vizinhança.")
    return df_nodes

def gerar_relatorio_final(df_nodes):
    """Gera um arquivo de texto com o resumo do processo de dedução."""
    print("--- Etapa Final: Gerando relatório de dedução ---")
    with open(ARQUIVO_RELATORIO_SAIDA, 'w', encoding='utf-8') as f:
        f.write("==============================================\n")
        f.write("=    RELATÓRIO DO PIPELINE DE DEDUÇÃO        =\n")
        f.write("==============================================\n\n")

        total_nos = len(df_nodes)
        nos_deduzidos = df_nodes['estado_deduzido'].notna().sum()
        f.write(f"Total de Nós Únicos Analisados: {total_nos}\n")
        f.write(f"Total de Nós com Estado Deduzido: {nos_deduzidos} ({nos_deduzidos/total_nos:.2%})\n\n")

        f.write("--- ESTATÍSTICAS POR MÉTODO DE DEDUÇÃO ---\n")
        stats = df_nodes['metodo_deducao'].value_counts()
        if stats.empty:
            f.write("Nenhum nó pôde ser classificado.\n")
        else:
            for metodo, contagem in stats.items():
                f.write(f"- {metodo}: {contagem} nós\n")
        
        f.write("\n--- NÓS SEM ESTADO DEFINIDO ---\n")
        nos_sem_estado = df_nodes[df_nodes['estado_deduzido'].isna()]
        if nos_sem_estado.empty:
            f.write("Todos os nós tiveram seu estado deduzido com sucesso!\n")
        else:
            f.write(f"Total: {len(nos_sem_estado)} nós\n")
            for _, row in nos_sem_estado.iterrows():
                f.write(f"- Nome: {row['nome']}, IP: {row['ip']}\n")
    print(f"✅ Relatório salvo em: {ARQUIVO_RELATORIO_SAIDA}")

# --- FUNÇÃO PRINCIPAL ---

def executar_pipeline_deducao():
    """Orquestra a execução de todas as etapas do pipeline de dedução."""
    # Validação dos arquivos de entrada
    if not os.path.exists(ARQUIVO_NOS_ENTRADA) or not os.path.exists(ARQUIVO_ARESTAS_ENTRADA):
        print(f"🚨 ERRO: Arquivos '{ARQUIVO_NOS_ENTRADA}' ou '{ARQUIVO_ARESTAS_ENTRADA}' não encontrados.")
        print("Execute o script 'generate_network_map.py' primeiro.")
        return
    
    # Etapa 0: Preparação
    print("--- Etapa 0: Carregando e preparando os dados ---")
    df_nodes = pd.read_csv(ARQUIVO_NOS_ENTRADA, index_col='id')
    df_edges = pd.read_csv(ARQUIVO_ARESTAS_ENTRADA)
    
    df_nodes['estado_deduzido'] = pd.NA
    df_nodes['metodo_deducao'] = pd.NA
    df_nodes['nivel_confianca'] = 0
    print("✅ Dados carregados com sucesso.\n")

    # Execução das Etapas do Pipeline
    df_nodes = etapa_1_ancoras_de_viagem(df_nodes)
    df_nodes = etapa_2_match_perfeito(df_nodes)
    df_nodes = etapa_3_regra_sanduiche(df_nodes, df_edges)

    # Etapa Final: Salvar resultados e gerar relatório
    print("\n--- Conclusão do Pipeline ---")
    df_nodes.to_csv(ARQUIVO_NOS_SAIDA)
    print(f"✅ Arquivo final de nós com estados salvo em: {ARQUIVO_NOS_SAIDA}")
    gerar_relatorio_final(df_nodes)

if __name__ == "__main__":
    executar_pipeline_deducao()