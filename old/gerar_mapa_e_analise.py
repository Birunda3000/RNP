import os
import json
import re
import pandas as pd
from collections import defaultdict

# --- CONFIGURAÇÕES GERAIS ---
PASTA_TRACEROUTE = os.path.join('data', 'raw', 'traceroute')
ARQUIVO_SAIDA_NOS = 'nodes_analysis.csv'
ARQUIVO_SAIDA_ARESTAS = 'edges.csv'
ARQUIVO_SAIDA_RELATORIO = 'relatorio_de_conflitos.txt'

ESTADOS_BR = {
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
    'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
    'sp', 'se', 'to'
}
SEPARADORES_HOSTNAME = r'[-._\s]'

# --- FUNÇÕES DAS REGRAS DE DEDUÇÃO ---

def regra_3_match_perfeito(hostname: str) -> str:
    """Aplica a Regra 3: Retorna a sigla do estado se houver exatamente 1 match perfeito."""
    if not isinstance(hostname, str) or not hostname:
        return ""
    
    partes = re.split(SEPARADORES_HOSTNAME, hostname.lower())
    candidatos = [p for p in partes if p in ESTADOS_BR]
    
    if len(candidatos) == 1:
        return candidatos[0].upper()
    return ""

def regra_4_inferencia_vizinhanca(node_info: dict, nodes_db: dict) -> str:
    """Aplica a Regra 4: Retorna o estado se todos os vizinhos definidos estiverem no mesmo estado."""
    estados_vizinhos_definidos = []
    for vizinho_key in node_info.get('vizinhos', set()):
        vizinho = nodes_db.get(vizinho_key, {})
        if vizinho.get('status_final') == 'DEFINIDO':
            estados_vizinhos_definidos.append(vizinho.get('estado_final'))

    if not estados_vizinhos_definidos:
        return ""

    if len(set(estados_vizinhos_definidos)) == 1:
        return estados_vizinhos_definidos[0]
        
    return ""

# --- FUNÇÃO PRINCIPAL DO PIPELINE ---

def executar_analise_completa():
    print("--- INICIANDO PIPELINE DE ANÁLISE E MAPEAMENTO DE REDE ---")

    if not os.path.exists(PASTA_TRACEROUTE):
        print(f"🚨 ERRO: Pasta de dados de traceroute não encontrada em '{PASTA_TRACEROUTE}'")
        return

    # ETAPA 1: Ingestão de Dados e Construção do Grafo
    # ===============================================
    print("\n[ETAPA 1/5] Lendo dados brutos e construindo o grafo...")
    nodes_db = {}
    edges = set()
    
    for filename in os.listdir(PASTA_TRACEROUTE):
        if not filename.endswith('.json'):
            continue
        
        filepath = os.path.join(PASTA_TRACEROUTE, filename)
        
        try: # Extrai origem/destino da viagem do nome do arquivo
            partes_nome_arquivo = filename.replace('.json', '').split('_to_')
            origem_viagem = partes_nome_arquivo[0].split('-')[1].lower()
            destino_viagem = partes_nome_arquivo[1].split('-')[1].lower()
        except IndexError:
            print(f"  [AVISO] Não foi possível deduzir a viagem do arquivo: {filename}. Pulando.")
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                all_traces = json.load(f)
            except json.JSONDecodeError:
                continue

        for trace in all_traces:
            hops = trace.get('val', [])
            if len(hops) < 1:
                continue

            # Processa os nós e arestas de cada trace
            for i in range(len(hops)):
                hop = hops[i]
                nome = hop.get('hostname', '').lower()
                ip = hop.get('ip', 'N/A')
                node_key = f"{nome}|{ip}"
                
                if node_key not in nodes_db:
                    nodes_db[node_key] = {'nome': nome, 'ip': ip, 'vizinhos': set()}
                
                if i > 0:
                    prev_hop = hops[i-1]
                    prev_nome = prev_hop.get('hostname', '').lower()
                    prev_ip = prev_hop.get('ip', 'N/A')
                    prev_node_key = f"{prev_nome}|{prev_ip}"
                    
                    edges.add(tuple(sorted((prev_node_key, node_key))))
                    nodes_db[node_key]['vizinhos'].add(prev_node_key)
                    nodes_db[prev_node_key]['vizinhos'].add(node_key)

            # Aplica Regras 1 e 2
            primeiro_hop = hops[0]
            primeiro_nome = primeiro_hop.get('hostname', '').lower()
            primeiro_ip = primeiro_hop.get('ip', 'N/A')
            primeiro_key = f"{primeiro_nome}|{primeiro_ip}"
            nodes_db[primeiro_key]['R1_POP_Origem'] = origem_viagem.upper()

            if len(hops) > 1:
                ultimo_hop = hops[-1]
                ultimo_nome = ultimo_hop.get('hostname', '').lower()
                ultimo_ip = ultimo_hop.get('ip', 'N/A')
                ultimo_key = f"{ultimo_nome}|{ultimo_ip}"
                nodes_db[ultimo_key]['R2_POP_Destino'] = destino_viagem.upper()

    print(f"✅ Grafo construído com {len(nodes_db)} nós e {len(edges)} arestas únicas.")

    # ETAPA 2: Aplicação das Regras de Dedução
    # ========================================
    print("\n[ETAPA 2/5] Aplicando regras de dedução...")
    for key, node in nodes_db.items():
        # Inicializa colunas
        node.setdefault('R1_POP_Origem', '')
        node.setdefault('R2_POP_Destino', '')
        
        # Aplica Regra 3
        node['R3_Hostname_MatchPerfeito'] = regra_3_match_perfeito(node['nome'])

    # ETAPA 3: Cálculo do Status Final (Iterativo para Regra 4)
    # ========================================================
    print("\n[ETAPA 3/5] Calculando status final e aplicando Regra 4 (vizinhos)...")
    for _ in range(5): # Loop para permitir que a Regra 4 se propague
        nodes_modificados_na_iteracao = 0
        for key, node in nodes_db.items():
            deducoes = [
                node.get('R1_POP_Origem'),
                node.get('R2_POP_Destino'),
                node.get('R3_Hostname_MatchPerfeito'),
                node.get('R4_Inferencia_Vizinhanca', '') # Pega o valor da iteração anterior
            ]
            deducoes_validas = [d for d in deducoes if d]
            set_deducoes = set(deducoes_validas)
            
            # Atualiza status e estado final preliminarmente
            if len(set_deducoes) == 1:
                node['status_final'] = 'DEFINIDO'
                node['estado_final'] = list(set_deducoes)[0]
            else: # Temporariamente indefinido para aplicar R4
                node['status_final'] = 'INDEFINIDO' 
                node['estado_final'] = ''

        # Agora, com status preliminares, tenta aplicar a R4
        for key, node in nodes_db.items():
            if not node.get('R1_POP_Origem') and not node.get('R2_POP_Destino') and not node.get('R3_Hostname_MatchPerfeito'):
                estado_r4 = regra_4_inferencia_vizinhanca(node, nodes_db)
                if estado_r4 and node.get('R4_Inferencia_Vizinhanca') != estado_r4:
                    node['R4_Inferencia_Vizinhanca'] = estado_r4
                    nodes_modificados_na_iteracao += 1
        
        if nodes_modificados_na_iteracao == 0:
            break # Estabilizou, pode sair do loop

    # Cálculo final do status
    for key, node in nodes_db.items():
        deducoes = [node.get(f'R{i+1}_{sufixo}') for i, sufixo in enumerate(['POP_Origem', 'POP_Destino', 'Hostname_MatchPerfeito', 'Inferencia_Vizinhanca'])]
        deducoes_validas = [d for d in deducoes if d]
        set_deducoes = set(deducoes_validas)
        
        if len(set_deducoes) == 1:
            node['status_final'] = 'DEFINIDO'
            node['estado_final'] = list(set_deducoes)[0]
        elif len(set_deducoes) > 1:
            node['status_final'] = 'CONFLITO'
            node['estado_final'] = ";".join(sorted(list(set_deducoes)))
        else:
            node['status_final'] = 'INDEFINIDO'
            node['estado_final'] = ''
    print("✅ Status final e Regra 4 aplicados.")

    # ETAPA 4: Geração do Relatório de Conflitos
    # ==========================================
    print("\n[ETAPA 4/5] Gerando relatório de conflitos...")
    with open(ARQUIVO_SAIDA_RELATORIO, 'w', encoding='utf-8') as f:
        f.write("=========================================================\n")
        f.write("=    ⚠️ ⚠️ ⚠️  RELATÓRIO DE CONFLITOS E AVISOS  ⚠️ ⚠️ ⚠️    =\n")
        f.write("=========================================================\n\n")
        
        # Conflito 1: Nós com status "CONFLITO"
        conflitos_status = {k: v for k, v in nodes_db.items() if v['status_final'] == 'CONFLITO'}
        f.write(f"--- 1. NÓS COM DEDUÇÕES CONFLITANTES ({len(conflitos_status)}) ---\n")
        if not conflitos_status:
            f.write("Nenhum nó com deduções conflitantes foi encontrado.\n")
        else:
            for key, node in conflitos_status.items():
                f.write(f"\nNó: {key}\n")
                f.write(f"  Estado Final Deduzido: {node['estado_final']}\n")
                f.write(f"  Deduções individuais:\n")
                f.write(f"    - R1 (Origem POP): '{node.get('R1_POP_Origem')}'\n")
                f.write(f"    - R2 (Destino POP): '{node.get('R2_POP_Destino')}'\n")
                f.write(f"    - R3 (Hostname): '{node.get('R3_Hostname_MatchPerfeito')}'\n")
                f.write(f"    - R4 (Vizinhos): '{node.get('R4_Inferencia_Vizinhanca', '')}'\n")
        
        # Conflito 2: IPs com múltiplos nomes ou estados
        ips_map = defaultdict(list)
        for key, node in nodes_db.items():
            ips_map[node['ip']].append(node)
        
        ips_conflitantes = {ip: nodes for ip, nodes in ips_map.items() if len(nodes) > 1}
        f.write(f"\n--- 2. IPS ASSOCIADOS A MÚLTIPLOS NÓS ÚNICOS ({len(ips_conflitantes)}) ---\n")
        if not ips_conflitantes:
            f.write("Nenhum IP conflitante foi encontrado.\n")
        else:
            for ip, nodes in ips_conflitantes.items():
                f.write(f"\nIP: {ip} está associado a {len(nodes)} entradas:\n")
                for node in nodes:
                    f.write(f"  - Nó: {node['nome']}|{ip}\n")
                    f.write(f"    Status: {node['status_final']}, Estado: '{node['estado_final']}'\n")

    print(f"✅ Relatório de conflitos salvo em '{ARQUIVO_SAIDA_RELATORIO}'.")
    
    # ETAPA 5: Geração dos Arquivos Finais
    # ====================================
    print("\n[ETAPA 5/5] Gerando arquivos CSV de saída...")
    # Nós
    df_nodes = pd.DataFrame.from_dict(nodes_db, orient='index')
    colunas_ordenadas = [
        'nome', 'ip', 'R1_POP_Origem', 'R2_POP_Destino', 
        'R3_Hostname_MatchPerfeito', 'R4_Inferencia_Vizinhanca', 
        'estado_final', 'status_final'
    ]
    df_nodes = df_nodes.reindex(columns=colunas_ordenadas).fillna('')
    df_nodes.to_csv(ARQUIVO_SAIDA_NOS, index_label='chave_unica_no')
    
    # Arestas
    with open(ARQUIVO_SAIDA_ARESTAS, 'w', newline='', encoding='utf-8') as f:
        writer = pd.DataFrame(list(edges), columns=['source', 'target'])
        writer.to_csv(f, index=False)
        
    print(f"✅ Arquivo de nós salvo em '{ARQUIVO_SAIDA_NOS}'.")
    print(f"✅ Arquivo de arestas salvo em '{ARQUIVO_SAIDA_ARESTAS}'.")
    print("\n--- PIPELINE FINALIZADO COM SUCESSO ---")

if __name__ == '__main__':
    executar_analise_completa()