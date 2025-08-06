import os
import json
import csv
from collections import defaultdict
"""
Script para identificar conflitos de IPs e hostnames em dados de traceroute.
Ele gera um mapa base com nós (IPs e hostnames) e arestas (conexões entre eles).
"""

# --- CONFIGURAÇÕES ---
PASTA_INPUT_RAW = os.path.join('data', 'raw', 'traceroute')
PASTA_OUTPUT = 'output'
ARQUIVO_SAIDA_NOS = os.path.join(PASTA_OUTPUT, 'nodes.csv')
ARQUIVO_SAIDA_ARESTAS = os.path.join(PASTA_OUTPUT, 'edges.csv')

def gerar_mapa_base_com_lista_nomes():
    """
    Versão atualizada que lê todos os dados brutos e armazena uma lista
    de todos os hostnames únicos associados a cada IP.
    """
    print("--- INICIANDO SCRIPT v3: GERAÇÃO DE MAPA BASE COM LISTA DE NOMES ---")

    if not os.path.exists(PASTA_INPUT_RAW):
        print(f"🚨 ERRO: A pasta de dados brutos '{PASTA_INPUT_RAW}' não foi encontrada.")
        return

    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    # --- MUDANÇA NA ESTRUTURA DE DADOS ---
    # defaultdict(set) cria um set vazio para um novo IP automaticamente.
    # Armazenará: {ip: {'nome1', 'nome2'}}
    nodes_por_ip = defaultdict(set)
    edges = set()

    print(f"🔎 Lendo e processando arquivos de '{PASTA_INPUT_RAW}'...")
    lista_arquivos = sorted([f for f in os.listdir(PASTA_INPUT_RAW) if f.endswith('.json')])
    print(f"  -> {len(lista_arquivos)} arquivos .json encontrados para processamento.")

    # Etapa 1: Coletar todos os nós e arestas, acumulando nomes
    for filename in lista_arquivos:
        filepath = os.path.join(PASTA_INPUT_RAW, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                content = f.read()
                if not content: continue
                dados_traces = json.loads(content)
            except json.JSONDecodeError:
                print(f"  [AVISO] Arquivo JSON inválido ou corrompido, pulando: {filename}")
                continue

            for trace in dados_traces:
                hops = trace.get('val', [])
                for i, hop in enumerate(hops):
                    ip = hop.get('ip')
                    hostname = hop.get('hostname', '')

                    if not ip: continue

                    # --- MUDANÇA NA LÓGICA DE COLETA ---
                    # Garante que o IP exista no dicionário. Se o hostname não for vazio,
                    # ele é adicionado ao set de nomes daquele IP.
                    if hostname:
                        nodes_por_ip[ip].add(hostname)
                    else:
                        # Garante que mesmo IPs sem nome sejam registrados.
                        # Acessar a chave no defaultdict já a cria se não existir.
                        nodes_por_ip[ip]

                    # Lógica de arestas permanece a mesma, baseada em IPs
                    if i > 0:
                        prev_ip = hops[i-1].get('ip')
                        if prev_ip:
                            edge = tuple(sorted((prev_ip, ip)))
                            edges.add(edge)

    print(f"📊 Processamento concluído. Encontrados {len(nodes_por_ip)} nós e {len(edges)} arestas únicas.")

    # Etapa 2: Gerar arquivos de saída
    print(f"✍️  Gerando arquivos de saída na pasta '{PASTA_OUTPUT}'...")

    ip_para_id = {ip: i for i, ip in enumerate(nodes_por_ip.keys())}

    # Gerar nodes.csv
    with open(ARQUIVO_SAIDA_NOS, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'nome', 'ip'])
        for ip, set_de_nomes in nodes_por_ip.items():
            node_id = ip_para_id[ip]
            # --- MUDANÇA NO FORMATO DE SAÍDA ---
            # Junta todos os nomes do set em uma única string, separados por ';'.
            # A ordenação garante que a saída seja sempre a mesma.
            nomes_str = ";".join(sorted(list(set_de_nomes)))
            writer.writerow([node_id, nomes_str, ip])

    # Gerar edges.csv (sem alterações na lógica)
    with open(ARQUIVO_SAIDA_ARESTAS, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source_id', 'target_id'])
        for ip1, ip2 in sorted(list(edges)):
            source_id = ip_para_id.get(ip1)
            target_id = ip_para_id.get(ip2)
            if source_id is not None and target_id is not None:
                writer.writerow([source_id, target_id])

    print(f"✅ Arquivos '{os.path.basename(ARQUIVO_SAIDA_NOS)}' e '{os.path.basename(ARQUIVO_SAIDA_ARESTAS)}' salvos com sucesso.")
    print("--- SCRIPT FINALIZADO ---")

if __name__ == '__main__':
    gerar_mapa_base_com_lista_nomes()