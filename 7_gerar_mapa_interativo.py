import pandas as pd
import plotly.graph_objects as go
import os
import random ### MUDANÇA: Importamos a biblioteca random

# --- CONFIGURAÇÕES ---
PASTA_PROCESSED = os.path.join('data', 'processed')
ARQUIVO_INPUT_NODES = os.path.join(PASTA_PROCESSED, 'nodes_chute_final.csv')
ARQUIVO_INPUT_EDGES = os.path.join(PASTA_PROCESSED, 'edges.csv')
ARQUIVO_SAIDA_MAPA = 'mapa_rede_interativo_v2.html' # Novo nome de arquivo

# Coordenadas aproximadas das capitais de cada estado para posicionar os nós
COORDENADAS_ESTADOS = {
    'AC': (-9.97, -67.81), 'AL': (-9.66, -35.73), 'AP': (0.03, -51.06),
    'AM': (-3.11, -60.02), 'BA': (-12.97, -38.50), 'CE': (-3.73, -38.52),
    'DF': (-15.79, -47.88), 'ES': (-20.31, -40.33), 'GO': (-16.68, -49.26),
    'MA': (-2.53, -44.30), 'MT': (-15.60, -56.09), 'MS': (-20.46, -54.62),
    'MG': (-19.91, -43.93), 'PA': (-1.45, -48.49), 'PB': (-7.11, -34.86),
    'PR': (-25.42, -49.27), 'PE': (-8.04, -34.88), 'PI': (-5.09, -42.80),
    'RJ': (-22.90, -43.17), 'RN': (-5.79, -35.20), 'RS': (-30.03, -51.22),
    'RO': (-8.76, -63.90), 'RR': (2.82, -60.67), 'SC': (-27.59, -48.54),
    'SP': (-23.55, -46.63), 'SE': (-10.94, -37.07), 'TO': (-10.21, -48.36)
}

### MUDANÇA: Função para aplicar a dispersão (jitter) ###
def aplicar_jitter(coord, intensidade=0.5):
    """ Adiciona um valor aleatório a uma coordenada para dispersão. """
    return coord + random.uniform(-intensidade, intensidade)

def gerar_mapa_interativo_v2():
    """
    Cria um mapa geográfico interativo da rede RNP usando Plotly,
    com dispersão (jitter) para evitar sobreposição de nós.
    """
    print("--- GERANDO MAPA INTERATIVO DA REDE (V2 - COM DISPERSÃO) ---")
    
    # Carrega os dados
    df_nodes = pd.read_csv(ARQUIVO_INPUT_NODES)
    df_edges = pd.read_csv(ARQUIVO_INPUT_EDGES)
    
    # Adiciona coordenadas a cada nó
    df_nodes['lat_base'] = df_nodes['estado_final'].map(lambda x: COORDENADAS_ESTADOS.get(x, (None, None))[0])
    df_nodes['lon_base'] = df_nodes['estado_final'].map(lambda x: COORDENADAS_ESTADOS.get(x, (None, None))[1])
    df_nodes.dropna(subset=['lat_base', 'lon_base'], inplace=True)

    ### MUDANÇA: Aplica o jitter nas coordenadas base ###
    df_nodes['latitude'] = df_nodes['lat_base'].apply(aplicar_jitter)
    df_nodes['longitude'] = df_nodes['lon_base'].apply(aplicar_jitter)
    
    # Cria um mapa de ID para as informações do nó
    mapa_nos = df_nodes.set_index('id').to_dict('index')

    # Cria as linhas das arestas no mapa (lógica inalterada)
    edge_traces = []
    for _, edge in df_edges.iterrows():
        source_id, target_id = edge['source_id'], edge['target_id']
        if source_id in mapa_nos and target_id in mapa_nos:
            source_node = mapa_nos[source_id]
            target_node = mapa_nos[target_id]
            
            edge_traces.append(go.Scattergeo(
                lon=[source_node['longitude'], target_node['longitude']],
                lat=[source_node['latitude'], target_node['latitude']],
                mode='lines',
                line=dict(width=0.7, color='#a8a8a8'),
                hoverinfo='none'
            ))

    # Cria os pontos dos nós no mapa (lógica inalterada)
    node_trace = go.Scattergeo(
        lon=df_nodes['longitude'],
        lat=df_nodes['latitude'],
        text=df_nodes.apply(lambda row: f"<b>IP:</b> {row['ip']}<br><b>Nome:</b> {row['nome']}<br><b>Estado:</b> {row['estado_final']}", axis=1),
        hoverinfo='text',
        mode='markers',
        marker=dict(
            color=df_nodes['estado_final'].astype('category').cat.codes,
            colorscale='Viridis',
            size=8,
            opacity=0.8,
            colorbar=dict(title='Estados (Codificados)')
        )
    )

    # Configura o layout do mapa (lógica inalterada)
    layout = go.Layout(
        title_text='Visualização Geográfica da Rede RNP (com Dispersão de Nós)',
        showlegend=False,
        geo=dict(
            scope='south america',
            projection_type='mercator',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            countrycolor='rgb(204, 204, 204)',
            lataxis_range=[-35, 6],
            lonaxis_range=[-75, -30]
        ),
        margin={"r":0,"t":40,"l":0,"b":0}
    )

    # Cria a figura e salva
    fig = go.Figure(data=edge_traces + [node_trace], layout=layout)
    fig.write_html(ARQUIVO_SAIDA_MAPA)
    print(f"✅ Mapa melhorado salvo com sucesso em '{ARQUIVO_SAIDA_MAPA}'.")

if __name__ == '__main__':
    gerar_mapa_interativo_v2()