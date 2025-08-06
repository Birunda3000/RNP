import os
import json
import re
import pandas as pd
from collections import defaultdict

# --- Configurações ---
ESTADOS_BR = {
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
    'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
    'sp', 'se', 'to'
}
TRACEROUTE_DIR = os.path.join('data', 'raw', 'traceroute')
ARQUIVO_SAIDA = 'nos_deduzidos.csv'

# --- Funções Auxiliares ---

def carregar_dados_brutos():
    """Lê todos os JSONs de traceroute e consolida os dados."""
    if not os.path.exists(TRACEROUTE_DIR):
        raise FileNotFoundError(f"Diretório não encontrado: {TRACEROUTE_DIR}")

    all_nodes = set()
    all_journeys = []
    graph = defaultdict(set)

    print("--- 1. Carregando e consolidando dados brutos de traceroute... ---")
    for filename in os.listdir(TRACEROUTE_DIR):
        if not filename.endswith('.json'):
            continue
        
        # Extrai estados da origem/destino da viagem do nome do arquivo
        try:
            parts = filename.replace('.json', '').split('_to_')
            origin_host, dest_host = parts[0], parts[1].split('_')[0]
            # Assumindo que a sigla do estado é o segundo fragmento do nome do host monipe
            origin_state = origin_host.split('-')[1]
            dest_state = dest_host.split('-')[1]
        except IndexError:
            print(f"  [AVISO] Não foi possível extrair estados do nome do arquivo: {filename}")
            continue

        filepath = os.path.join(TRACEROUTE_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"  [AVISO] Arquivo JSON inválido: {filename}")
                continue

        for trace in data:
            path = []
            for hop in trace.get('val', []):
                ip = hop.get('ip')
                if not ip: continue
                # Garante que o hostname seja uma string, vazia se não existir
                hostname = hop.get('hostname', '').lower()
                node = (hostname, ip)
                path.append(node)
                all_nodes.add(node)
            
            if path:
                all_journeys.append({'path': path, 'origin': origin_state, 'destination': dest_state})
                # Constrói o grafo
                for i in range(len(path) - 1):
                    graph[path[i]].add(path[i+1])
                    graph[path[i+1]].add(path[i]) # Grafo não direcionado

    print(f"✅ Dados consolidados: {len(all_nodes)} nós únicos e {len(all_journeys)} viagens encontradas.")
    return pd.DataFrame(list(all_nodes), columns=['hostname', 'ip']), all_journeys, graph


def aplicar_regra_1(df, journeys):
    """Regra 1: Âncoras de Viagem (primeiro e último salto)."""
    print("--- 2. Aplicando Regra 1 (Âncoras de Viagem)... ---")
    deductions = defaultdict(set)
    for journey in journeys:
        path = journey['path']
        if not path: continue
        # Primeiro nó pega o estado de origem
        deductions[path[0]].add(journey['origin'])
        # Último nó pega o estado de destino
        deductions[path[-1]].add(journey['destination'])
    
    # Aplica deduções, pegando o primeiro estado encontrado (conflitos internos são raros aqui)
    df['estado_regra_1'] = df.apply(lambda row: list(deductions.get(tuple(row[['hostname', 'ip']]), {''}))[0], axis=1)
    return df


def aplicar_regra_3(df):
    """Regra 3: Match Perfeito de Hostname."""
    print("--- 3. Aplicando Regra 3 (Match Perfeito de Hostname)... ---")
    
    def find_perfect_match(hostname):
        if not hostname: return ''
        # Adiciona '+' ao regex para tratar múltiplos delimitadores juntos
        parts = re.split(r'[-._\s]+', hostname.lower())
        found_states = [p for p in parts if p in ESTADOS_BR]
        return found_states[0] if len(found_states) == 1 else ''
        
    df['estado_regra_3'] = df['hostname'].apply(find_perfect_match)
    return df


def aplicar_regra_2(df, graph):
    """Regra 2: Inferência por Vizinhança (Sanduíche)."""
    print("--- 4. Aplicando Regra 2 (Inferência por Vizinhança)... ---")
    df['estado_regra_2'] = ''
    
    # Executa em loop até não haver mais mudanças
    while True:
        mudancas_feitas = 0
        
        # Mapeamento atual de nós definidos para seus estados
        # Um nó é 'definido' se tiver um estado inequívoco de qualquer regra
        mapa_estados_atuais = {}
        temp_df = df.copy()
        temp_df['temp_final'], temp_df['temp_status'] = zip(*temp_df.apply(calcular_status_linha, axis=1))

        for idx, row in temp_df.iterrows():
            if row['temp_status'] == 'DEFINIDO':
                mapa_estados_atuais[tuple(row[['hostname', 'ip']])] = row['temp_final']

        # Itera para encontrar novos nós para deduzir
        for index, row in df.iterrows():
            node = tuple(row[['hostname', 'ip']])
            # Só aplica se a regra 2 ainda não definiu um estado para este nó
            if row['estado_regra_2']:
                continue

            neighbors = graph.get(node, set())
            defined_neighbors_states = {mapa_estados_atuais.get(n) for n in neighbors if n in mapa_estados_atuais}
            
            # Remove None se algum vizinho não estiver no mapa
            defined_neighbors_states.discard(None)

            # Se todos os vizinhos definidos estão no mesmo estado
            if len(defined_neighbors_states) == 1:
                deduced_state = defined_neighbors_states.pop()
                df.loc[index, 'estado_regra_2'] = deduced_state
                mudancas_feitas += 1
        
        print(f"  -> Iteração concluída. {mudancas_feitas} novos nós deduzidos.")
        if mudancas_feitas == 0:
            break
            
    return df


def calcular_status_linha(row):
    """Calcula o status e o estado final para uma única linha."""
    deductions = {row[col] for col in ['estado_regra_1', 'estado_regra_2', 'estado_regra_3'] if pd.notna(row[col]) and row[col] != ''}
    
    if len(deductions) == 1:
        return list(deductions)[0], 'DEFINIDO'
    elif len(deductions) > 1:
        return ';'.join(sorted(list(deductions))), 'CONFLITO'
    else:
        return '', 'INDEFINIDO'


def analisar_conflitos_ip(df):
    """Verifica se um mesmo IP está associado a múltiplos nomes ou estados definidos."""
    print("--- 6. Verificando consistência de IPs... ---")
    
    # Filtra apenas nós com estado definido para a análise de conflito de estado
    df_definidos = df[df['status_final'] == 'DEFINIDO'].copy()
    
    ips_com_multiplos_nomes = df.groupby('ip')['hostname'].nunique()
    ips_com_multiplos_nomes = ips_com_multiplos_nomes[ips_com_multiplos_nomes > 1]

    ips_com_multiplos_estados = df_definidos.groupby('ip')['estado_final'].nunique()
    ips_com_multiplos_estados = ips_com_multiplos_estados[ips_com_multiplos_estados > 1]
    
    if ips_com_multiplos_nomes.empty and ips_com_multiplos_estados.empty:
        print("✅ Verificação de consistência concluída. Nenhum conflito de IP encontrado.")
        return

    print("\n\n/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\")
    print("    A  L  E  R  T  A   G  I  G  A  N  T  E   D E   C O N F L I T O")
    print("/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\")
    
    if not ips_com_multiplos_nomes.empty:
        print("\n  --- IPs associados a MÚLTIPLOS HOSTNAMES ---")
        for ip, count in ips_com_multiplos_nomes.items():
            nomes = df[df['ip'] == ip]['hostname'].unique()
            print(f"\n  [IP]: {ip} está associado a {count} nomes:")
            for nome in nomes:
                print(f"    - '{nome}'")

    if not ips_com_multiplos_estados.empty:
        print("\n  --- IPs associados a MÚLTIPLOS ESTADOS DEFINIDOS ---")
        for ip, count in ips_com_multiplos_estados.items():
            detalhes = df_definidos[df_definidos['ip'] == ip]
            print(f"\n  [IP]: {ip} tem deduções conflitantes para {count} estados:")
            for _, row in detalhes.iterrows():
                print(f"    - Hostname: '{row['hostname']}' -> Estado: {row['estado_final']}")

    print("\n/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\/!\\")

# --- Pipeline Principal ---
if __name__ == "__main__":
    try:
        # Etapa 1: Carregar e preparar os dados
        df_nodes, journeys, graph = carregar_dados_brutos()
        
        # Etapas 2 e 3: Aplicar regras de alta confiança primeiro
        df_nodes = aplicar_regra_1(df_nodes, journeys)
        df_nodes = aplicar_regra_3(df_nodes)
        
        # Etapa 4: Aplicar regra de inferência iterativamente
        df_nodes = aplicar_regra_2(df_nodes, graph)
        
        # Etapa 5: Calcular o status final de cada nó
        print("--- 5. Consolidando resultados e definindo status final... ---")
        df_nodes['estado_final'], df_nodes['status_final'] = zip(*df_nodes.apply(calcular_status_linha, axis=1))
        
        # Salvar o resultado
        df_nodes.to_csv(ARQUIVO_SAIDA, index=False)
        print(f"✅ Pipeline concluído. Resultado salvo em '{ARQUIVO_SAIDA}'.")

        # Etapa 6: Verificação final de consistência
        analisar_conflitos_ip(df_nodes)

    except FileNotFoundError as e:
        print(f"\n🚨 ERRO CRÍTICO: {e}. Verifique o caminho e se os dados brutos existem.")
    except Exception as e:
        print(f"\n🚨 ERRO INESPERADO: Ocorreu um erro durante a execução do pipeline: {e}")