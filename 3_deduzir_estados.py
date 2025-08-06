import os
import json
import re
import pandas as pd

# --- CONFIGURAÇÕES ---
PASTA_OUTPUT = 'output'
PASTA_INPUT_RAW = os.path.join('data', 'raw', 'traceroute')
ARQUIVO_INPUT_NOS = os.path.join(PASTA_OUTPUT, 'nodes.csv')
ARQUIVO_SAIDA_DEDUCOES = os.path.join(PASTA_OUTPUT, 'nodes_com_deducoes.csv')

ESTADOS_BR = {
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
    'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
    'sp', 'se', 'to'
}
SEPARADORES_HOSTNAME = r'[-._\s]'

# --- FUNÇÕES DAS REGRAS ---

def aplicar_regra_match_perfeito(hostname):
    """
    Aplica a Regra 3. Retorna a sigla do estado se encontrar exatamente um
    match perfeito no nome do host. Caso contrário, retorna uma string vazia.
    """
    if not isinstance(hostname, str) or not hostname:
        return ''
    
    # Converte para minúsculas para análise case-insensitive
    partes = re.split(SEPARADORES_HOSTNAME, hostname.lower())
    
    # Encontra as partes que são exatamente uma sigla de estado
    candidatos = [p for p in partes if p in ESTADOS_BR]
    
    # A regra é clara: exatamente um candidato
    if len(candidatos) == 1:
        return candidatos[0].upper()
    
    return ''

def calcular_status_final(row):
    """
    Analisa os resultados das regras para uma linha (nó) e determina o
    status final: Definido, Conflito ou Indefinido.
    """
    # Coleta todas as deduções não vazias daquele nó
    deducoes = [
        row['No de inicio'],
        row['No de fim'],
        row['Match perfeito']
    ]
    deducoes_validas = [d for d in deducoes if pd.notna(d) and d != '']
    
    # Cria um conjunto de deduções únicas
    set_deducoes = set(deducoes_validas)
    
    if len(set_deducoes) == 1:
        # Todas as deduções (uma ou mais) apontam para o mesmo estado
        status = 'Definido'
        estado_final = list(set_deducoes)[0]
    elif len(set_deducoes) > 1:
        # Encontramos deduções para estados diferentes
        status = 'Conflito'
        estado_final = ";".join(sorted(list(set_deducoes)))
    else: # len(set_deducoes) == 0
        # Nenhuma regra conseguiu deduzir um estado
        status = 'Indefinido'
        estado_final = ''
        
    return pd.Series([estado_final, status])

# --- SCRIPT PRINCIPAL ---

def deduzir_estados():
    print("--- INICIANDO SCRIPT DE DEDUÇÃO DE ESTADOS ---")

    # Etapa 1: Carregar dados base
    try:
        df_nodes = pd.read_csv(ARQUIVO_INPUT_NOS)
    except FileNotFoundError:
        print(f"🚨 ERRO: Arquivo base de nós '{ARQUIVO_INPUT_NOS}' não encontrado.")
        print("   -> Execute o script '2_gerar_mapa_base_revisado.py' primeiro.")
        return
    
    print(f"✅ Arquivo de nós carregado com {len(df_nodes)} registros.")

    # Etapa 2: Aplicar Regras 1 e 2 (Nó de Início e Fim)
    print("🔎 Aplicando Regras 1 e 2 (Nó de Início e Fim)...")
    df_nodes['No de inicio'] = ''
    df_nodes['No de fim'] = ''
    
    # Usar o IP como índice para atualizações rápidas
    df_nodes.set_index('ip', inplace=True)
    
    lista_arquivos = [f for f in os.listdir(PASTA_INPUT_RAW) if f.endswith('.json')]
    for filename in lista_arquivos:
        filepath = os.path.join(PASTA_INPUT_RAW, filename)
        
        try:
            partes_nome = filename.replace('.json', '').split('_to_')
            origem_viagem = partes_nome[0].split('-')[1].upper()
            destino_viagem = partes_nome[1].split('-')[1].upper()
        except IndexError:
            continue

        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                if not content: continue
                dados_traces = json.loads(content)
            except json.JSONDecodeError:
                continue

            for trace in dados_traces:
                hops = trace.get('val', [])
                if len(hops) > 0:
                    primeiro_ip = hops[0].get('ip')
                    if primeiro_ip in df_nodes.index:
                        df_nodes.loc[primeiro_ip, 'No de inicio'] = origem_viagem
                
                if len(hops) > 1:
                    ultimo_ip = hops[-1].get('ip')
                    if ultimo_ip in df_nodes.index:
                        df_nodes.loc[ultimo_ip, 'No de fim'] = destino_viagem
                        
    df_nodes.reset_index(inplace=True) # Volta 'ip' a ser uma coluna normal

    # Etapa 3: Aplicar Regra 3 (Match Perfeito)
    print("🔎 Aplicando Regra 3 (Match Perfeito no Hostname)...")
    df_nodes['Match perfeito'] = df_nodes['nome'].apply(aplicar_regra_match_perfeito)

    # Etapa 4: Calcular o Status e Estado Final
    print("📊 Calculando o status e estado final para cada nó...")
    df_nodes[['estado_final', 'status_final']] = df_nodes.apply(calcular_status_final, axis=1)

    # Etapa 5: Salvar o resultado
    colunas_ordenadas = [
        'id', 'nome', 'ip', 'No de inicio', 'No de fim', 'Match perfeito', 
        'estado_final', 'status_final'
    ]
    df_nodes = df_nodes[colunas_ordenadas]
    df_nodes.to_csv(ARQUIVO_SAIDA_DEDUCOES, index=False)
    
    print("\n--- SCRIPT FINALIZADO ---")
    print(f"✅ Análise de dedução salva com sucesso em '{ARQUIVO_SAIDA_DEDUCOES}'.")
    
    # Exibe um resumo dos resultados
    print("\nResumo dos Status Finais:")
    print(df_nodes['status_final'].value_counts())

if __name__ == '__main__':
    deduzir_estados()