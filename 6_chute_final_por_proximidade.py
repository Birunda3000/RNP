import pandas as pd
import os
from collections import Counter

# --- CONFIGURAÇÕES ---
PASTA_PROCESSED = os.path.join('data', 'processed')
ARQUIVO_INPUT_COMPLETO = os.path.join(PASTA_PROCESSED, 'nodes_final.csv')
ARQUIVO_INPUT_EDGES = os.path.join(PASTA_PROCESSED, 'edges.csv')
ARQUIVO_SAIDA_CHUTE = os.path.join(PASTA_PROCESSED, 'nodes_chute_final.csv')

def chute_final():
    """
    Script 'fim do mundo' que força uma localização para nós restantes,
    usando uma análise de vizinhança estendida (2º grau).
    """
    print("--- ☢️  INICIANDO SCRIPT 'CHUTE FINAL' ☢️ ---")
    print("AVISO: Os resultados deste script são especulativos e baseados em inferência agressiva.")

    # --- Passo 1: Carregar os dados ---
    if not os.path.exists(ARQUIVO_INPUT_COMPLETO) or not os.path.exists(ARQUIVO_INPUT_EDGES):
        print(f"🚨 ERRO: Certifique-se de que '{os.path.basename(ARQUIVO_INPUT_COMPLETO)}' e "
              f"'{os.path.basename(ARQUIVO_INPUT_EDGES)}' existem.")
        return

    df_nodes = pd.read_csv(ARQUIVO_INPUT_COMPLETO)
    df_edges = pd.read_csv(ARQUIVO_INPUT_EDGES)
    print(f"📖 Lidos {len(df_nodes)} nós e {len(df_edges)} arestas.")

    # --- Passo 2: Preparar mapas de consulta ---
    mapa_id_para_estado = pd.Series(df_nodes.estado_final.values, index=df_nodes.id).to_dict()
    vizinhanca = {node_id: [] for node_id in df_nodes['id']}
    for _, edge in df_edges.iterrows():
        source, target = edge['source_id'], edge['target_id']
        if source in vizinhanca and target in vizinhanca:
            vizinhanca[source].append(target)
            vizinhanca[target].append(source)
    print("🗺️  Mapa da rede construído.")

    # --- Passo 3: Aplicar o chute ---
    df_nodes['estado_chute'] = df_nodes['estado_final']
    df_nodes['justificativa_chute'] = ''
    nodes_chutados = 0

    for index, node in df_nodes.iterrows():
        estado_atual = node['estado_final']
        if not (estado_atual == "Desconhecido" or str(estado_atual).startswith("Ambíguo")):
            continue

        node_id = node['id']
        
        # Coleta vizinhos de 1º e 2º grau
        vizinhos_1o_grau = set(vizinhanca.get(node_id, []))
        vizinhos_2o_grau = set()
        for vizinho in vizinhos_1o_grau:
            vizinhos_2o_grau.update(vizinhanca.get(vizinho, []))
        
        # Remove o próprio nó e os vizinhos de 1º grau da lista de 2º grau
        vizinhos_2o_grau.discard(node_id)
        vizinhos_2o_grau -= vizinhos_1o_grau
        
        # Votação na vizinhança estendida
        votos_vizinhanca = []
        for vizinho_id in list(vizinhos_1o_grau) + list(vizinhos_2o_grau):
            estado_vizinho = mapa_id_para_estado.get(vizinho_id)
            if estado_vizinho and estado_vizinho != "Desconhecido" and not str(estado_vizinho).startswith("Ambíguo"):
                votos_vizinhanca.append(estado_vizinho)

        if not votos_vizinhanca:
            df_nodes.loc[index, 'justificativa_chute'] = "Não foi possível chutar: sem vizinhos resolvidos em até 2 graus."
            continue

        contagem = Counter(votos_vizinhanca)
        vencedores = contagem.most_common()
        estado_vencedor, max_votos = vencedores[0]

        # Verifica se há empate
        empates = [v[0] for v in vencedores if v[1] == max_votos]
        
        justificativa = f"Chute por vizinhança de 2º grau. Votos: {dict(contagem)}"
        
        if len(empates) > 1:
            # DESEMPATE FINAL: ORDEM ALFABÉTICA
            estado_vencedor = sorted(empates)[0]
            justificativa += f". Empate resolvido alfabeticamente -> {estado_vencedor}"

        df_nodes.loc[index, 'estado_chute'] = estado_vencedor
        df_nodes.loc[index, 'justificativa_chute'] = justificativa
        nodes_chutados += 1
        
    print(f"💥 'Balde chutado'. {nodes_chutados} nós tiveram um estado forçado.")
    
    # Reorganiza as colunas para clareza
    df_final = df_nodes.drop(columns=['estado_final'])
    df_final = df_final.rename(columns={'estado_chute': 'estado_final'})
    
    df_final.to_csv(ARQUIVO_SAIDA_CHUTE, index=False, encoding='utf-8')
    print(f"✅ O mapa de nós mais completo (e especulativo) foi salvo em '{os.path.basename(ARQUIVO_SAIDA_CHUTE)}'.")

if __name__ == '__main__':
    chute_final()