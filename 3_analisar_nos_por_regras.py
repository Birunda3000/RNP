import pandas as pd
import os
import re
import json
from collections import defaultdict
from typing import List, Set, Dict

# --- CONFIGURAÇÕES ---
PASTA_RAW = os.path.join('data', 'raw', 'traceroute') # Caminho para os JSONs brutos
PASTA_PROCESSED = os.path.join('data', 'processed')
ARQUIVO_INPUT_NOS = os.path.join(PASTA_PROCESSED, 'nodes.csv')
ARQUIVO_SAIDA_ANALISE = os.path.join(PASTA_PROCESSED, 'nodes_analisado.csv')

# Lista de siglas de estados brasileiros para validação
SIGLAS_ESTADOS = {
    'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
    'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
    'sp', 'se', 'to'
}

# --- NOVA FUNÇÃO PARA PROCESSAR REGRAS DE CONTEXTO ---

def processar_regras_de_contexto() -> Dict:
    """
    Varre os arquivos JSON brutos para aplicar as regras 1 e 2.
    Extrai origem/destino do nome do arquivo e mapeia para o primeiro/último IP do trace.
    """
    print("Pre-processando regras de contexto (Regra 1 e 2)...")
    resultados = defaultdict(lambda: {"regra1": set(), "regra2": set()})
    
    # Padrão para extrair 'ac' e 'am' de 'monipe-ac-atraso_to_monipe-am-atraso_...'
    padrao_nome_arquivo = re.compile(r'monipe-([a-z]{2})-atraso_to_monipe-([a-z]{2})-atraso')

    if not os.path.exists(PASTA_RAW):
        print(f"  [AVISO] Pasta de dados brutos '{PASTA_RAW}' não encontrada. Pulando regras 1 e 2.")
        return {}

    for filename in os.listdir(PASTA_RAW):
        if not filename.endswith('.json'):
            continue

        match = padrao_nome_arquivo.match(filename)
        if not match:
            continue

        estado_origem, estado_destino = match.groups()

        filepath = os.path.join(PASTA_RAW, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                dados_traces = json.load(f)
            except json.JSONDecodeError:
                continue # Pula arquivos JSON malformados

            for trace in dados_traces:
                hops = trace.get('val', [])
                
                # Encontra primeiro e último IP válido no trace
                primeiro_ip = next((hop.get('ip') for hop in hops if hop.get('ip')), None)
                ultimo_ip = next((hop.get('ip') for hop in reversed(hops) if hop.get('ip')), None)

                if primeiro_ip:
                    resultados[primeiro_ip]["regra1"].add(estado_origem.upper())
                
                if ultimo_ip:
                    resultados[ultimo_ip]["regra2"].add(estado_destino.upper())

    print(f"  -> Contexto processado para {len(resultados)} IPs.")
    return resultados

# --- FUNÇÕES DAS REGRAS (SEM ALTERAÇÃO) ---

def aplicar_regra3_match_perfeito(hostnames: List[str]) -> List[str]:
    estados_deduzidos: Set[str] = set()
    for nome in hostnames:
        partes = re.split(r'[._-]', nome.lower())
        for parte in partes:
            if parte in SIGLAS_ESTADOS:
                estados_deduzidos.add(parte.upper())
    return sorted(list(estados_deduzidos))

def aplicar_regra4_padrao_monipe(hostnames: List[str]) -> List[str]:
    estados_deduzidos: Set[str] = set()
    padrao = re.compile(r'monipe-([a-z]{2})-atraso')
    for nome in hostnames:
        matches = padrao.findall(nome.lower())
        for sigla in matches:
            if sigla in SIGLAS_ESTADOS:
                estados_deduzidos.add(sigla.upper())
    return sorted(list(estados_deduzidos))

def aplicar_regra5_padrao_prefixo_local(hostnames: List[str]) -> List[str]:
    estados_deduzidos: Set[str] = set()
    padrao = re.compile(r'(?:c|cr|mx|b|lan)([a-z]{2})\d*')
    for nome in hostnames:
        partes = re.split(r'[._-]', nome.lower())
        for parte in partes:
            matches = padrao.findall(parte)
            for sigla in matches:
                if sigla in SIGLAS_ESTADOS:
                    estados_deduzidos.add(sigla.upper())
    return sorted(list(estados_deduzidos))

def aplicar_regra6_padrao_pop(hostnames: List[str]) -> List[str]:
    estados_deduzidos: Set[str] = set()
    padrao = re.compile(r'pop-([a-z]{2})|([a-z]{2})-pop')
    for nome in hostnames:
        matches = padrao.findall(nome.lower())
        for match in matches:
            sigla = next((s for s in match if s), None)
            if sigla and sigla in SIGLAS_ESTADOS:
                estados_deduzidos.add(sigla.upper())
    return sorted(list(estados_deduzidos))

def aplicar_regra7_conexoes_externas(hostnames: List[str]) -> List[str]:
    return []

# --- FUNÇÃO PRINCIPAL (MODIFICADA) ---

def analisar_nos():
    print("--- INICIANDO SCRIPT DE ANÁLISE DE NÓS POR REGRAS ---")

    # Passo 1: Pré-processar os JSONs para as regras de contexto
    resultados_contexto = processar_regras_de_contexto()

    # Passo 2: Carregar o arquivo de nós principal
    if not os.path.exists(ARQUIVO_INPUT_NOS):
        print(f"🚨 ERRO: Arquivo de entrada '{ARQUIVO_INPUT_NOS}' não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_INPUT_NOS)
    df['nome'] = df['nome'].fillna('')

    print(f"📖 Lendo {len(df)} nós de '{os.path.basename(ARQUIVO_INPUT_NOS)}'.")
    print("🔍 Aplicando regras de dedução de localidade...")
    
    # Passo 3: Aplicar regras de contexto (1 e 2) usando os resultados pré-processados
    df['regra1: primeiro no'] = df['ip'].apply(
        lambda ip: sorted(list(resultados_contexto.get(ip, {}).get("regra1", set())))
    )
    df['regra2: ultimo no'] = df['ip'].apply(
        lambda ip: sorted(list(resultados_contexto.get(ip, {}).get("regra2", set())))
    )
    
    # Passo 4: Aplicar regras baseadas em hostname (3 a 7)
    regras_hostname = {
        "regra3: match perfeito": aplicar_regra3_match_perfeito,
        "regra4: analise avançada de string padrão 1": aplicar_regra4_padrao_monipe,
        "regra5: analise avançada de string padrão 2": aplicar_regra5_padrao_prefixo_local,
        "regra6: analise avançada de string padrão 3": aplicar_regra6_padrao_pop,
        "regra7: analise avançada de string padrão 4": aplicar_regra7_conexoes_externas
    }

    for nome_coluna, funcao_regra in regras_hostname.items():
        df[nome_coluna] = df['nome'].apply(lambda x: funcao_regra(x.split(';')))

    # Passo 5: Salvar o resultado final
    print(f"💾 Salvando resultados em '{os.path.basename(ARQUIVO_SAIDA_ANALISE)}'...")
    df.to_csv(ARQUIVO_SAIDA_ANALISE, index=False, encoding='utf-8')

    print("✅ Análise concluída com sucesso!")
    print("--- SCRIPT FINALIZADO ---")


if __name__ == '__main__':
    analisar_nos()