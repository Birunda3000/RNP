import pandas as pd
import os
from collections import Counter

# --- CONFIGURAÇÕES ---
PASTA_PROCESSED = os.path.join('data', 'processed')
ARQUIVO_INPUT_CONSOLIDADO = os.path.join(PASTA_PROCESSED, 'nodes_consolidado.csv')
ARQUIVO_INPUT_EDGES = os.path.join(PASTA_PROCESSED, 'edges.csv')
ARQUIVO_SAIDA_FINAL = os.path.join(PASTA_PROCESSED, 'nodes_final.csv')

def resolver_por_vizinhos():
    """
    Script final que usa a topologia da rede para resolver nós com
    localização 'Desconhecida' ou 'Ambígua'.
    """
    print("--- INICIANDO SCRIPT DE RESOLUÇÃO POR VIZINHANÇA ---")

    # --- Passo 1: Carregar os dados ---
    if not os.path.exists(ARQUIVO_INPUT_CONSOLIDADO) or not os.path.exists(ARQUIVO_INPUT_EDGES):
        print(f"🚨 ERRO: Certifique-se de que '{os.path.basename(ARQUIVO_INPUT_CONSOLIDADO)}' e "
              f"'{os.path.basename(ARQUIVO_INPUT_EDGES)}' existem na pasta '{PASTA_PROCESSED}'.")
        return

    df_nodes = pd.read_csv(ARQUIVO_INPUT_CONSOLIDADO)
    df_edges = pd.read_csv(ARQUIVO_INPUT_EDGES)
    print(f"📖 Lidos {len(df_nodes)} nós e {len(df_edges)} arestas.")

    # --- Passo 2: Preparar estruturas de dados para consulta rápida ---

    # Cria um mapa de ID para Estado para consulta rápida da localização de um vizinho
    mapa_id_para_estado = pd.Series(df_nodes.estado_consolidado.values, index=df_nodes.id).to_dict()

    # Cria uma lista de adjacências (um dicionário de vizinhos) para o grafo
    vizinhanca = {node_id: [] for node_id in df_nodes['id']}
    for _, edge in df_edges.iterrows():
        source = edge['source_id']
        target = edge['target_id']
        if source in vizinhanca and target in vizinhanca:
            vizinhanca[source].append(target)
            vizinhanca[target].append(source)
    print("🗺️  Mapa da rede e vizinhança construídos.")

    # --- Passo 3: Iterar e resolver ambiguidades ---
    novos_estados = []
    novas_justificativas = []
    nodes_resolvidos = 0

    print("🔍 Analisando nós 'Desconhecidos' e 'Ambíguos'...")
    for _, node in df_nodes.iterrows():
        estado_atual = node['estado_consolidado']
        justificativa_atual = node['justificativa']
        
        # Se o estado já é conhecido e não é ambíguo, mantém como está
        if not (estado_atual == "Desconhecido" or str(estado_atual).startswith("Ambíguo")):
            novos_estados.append(estado_atual)
            novas_justificativas.append(justificativa_atual)
            continue
        
        node_id = node['id']
        ids_vizinhos = vizinhanca.get(node_id, [])
        
        # Coleta os estados dos vizinhos que já estão resolvidos
        estados_vizinhos = []
        for vizinho_id in ids_vizinhos:
            estado_vizinho = mapa_id_para_estado.get(vizinho_id)
            if estado_vizinho and estado_vizinho != "Desconhecido" and not str(estado_vizinho).startswith("Ambíguo"):
                estados_vizinhos.append(estado_vizinho)

        # Se não há vizinhos resolvidos, não há o que fazer
        if not estados_vizinhos:
            novos_estados.append(estado_atual) # Mantém o estado original
            novas_justificativas.append(justificativa_atual)
            continue
            
        # Contagem de votos
        contagem = Counter(estados_vizinhos)
        estado_majoritario, votos = contagem.most_common(1)[0]
        
        # Verifica se há empate. Se houver mais de um com a mesma contagem máxima, é um empate.
        empates = [v for v in contagem.values() if v == votos]
        
        if len(empates) > 1:
            # Em caso de empate, mantém o estado original
            novos_estados.append(estado_atual)
            novas_justificativas.append(justificativa_atual)
        else:
            # Sucesso! Encontramos um estado majoritário
            nodes_resolvidos += 1
            nova_justificativa = f"Votação dos vizinhos: {dict(contagem)}"
            novos_estados.append(estado_majoritario)
            novas_justificativas.append(nova_justificativa)

    # --- Passo 4: Atualizar o DataFrame e salvar ---
    df_nodes['estado_final'] = novos_estados
    df_nodes['justificativa_final'] = novas_justificativas
    
    print(f"🗳️  Votação concluída. {nodes_resolvidos} nós foram resolvidos pela análise de vizinhança.")
    
    # Reordenar colunas para o arquivo final
    cols_finais = [
        'id', 'ip', 'nome', 'estado_final', 'confianca_score', 
        'justificativa_final', 'estado_consolidado', 'justificativa'
    ]
    df_final = df_nodes[[col for col in cols_finais if col in df_nodes.columns] + 
                        [col for col in df_nodes.columns if col not in cols_finais]]

    df_final.to_csv(ARQUIVO_SAIDA_FINAL, index=False, encoding='utf-8')
    print(f"✅ Análise finalizada. Resultados salvos em '{os.path.basename(ARQUIVO_SAIDA_FINAL)}'.")
    print("--- PROJETO CONCLUÍDO ---")

if __name__ == '__main__':
    resolver_por_vizinhos()