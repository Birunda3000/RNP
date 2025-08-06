import os
import json
import csv
import itertools
from collections import defaultdict

"""
Script para identificar conflitos de IPs e hostnames em dados de traceroute.
Ele vasculha todos os arquivos JSON na pasta 'data/raw/traceroute/',
procura por IPs associados a múltiplos hostnames e salva os pares conflitantes
em um arquivo CSV.
"""

# --- CONFIGURAÇÕES ---
PASTA_INPUT_RAW = os.path.join('data', 'raw', 'traceroute')
PASTA_OUTPUT = 'output'
ARQUIVO_SAIDA_CSV = os.path.join(PASTA_OUTPUT, 'ip_hostname_conflicts.csv')

def identificar_conflitos_ip_hostname():
    """
    Vasculha todos os dados brutos de traceroute para encontrar IPs associados
    a mais de um hostname único e salva os pares conflitantes em um CSV.
    """
    print("--- INICIANDO SCRIPT DE IDENTIFICAÇÃO DE CONFLITOS (IP x Hostname) ---")

    # Verifica se a pasta de entrada existe
    if not os.path.exists(PASTA_INPUT_RAW):
        print(f"🚨 ERRO: A pasta de dados brutos '{PASTA_INPUT_RAW}' não foi encontrada.")
        return

    # Garante que a pasta de saída exista
    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    # Dicionário para armazenar todos os hostnames encontrados para cada IP.
    # Usar um set garante que os hostnames para cada IP sejam únicos.
    ip_para_hostnames = defaultdict(set)

    print(f"🔎 Vasculhando arquivos em '{PASTA_INPUT_RAW}'...")
    lista_arquivos = [f for f in os.listdir(PASTA_INPUT_RAW) if f.endswith('.json')]
    
    if not lista_arquivos:
        print(f"🚨 AVISO: Nenhum arquivo .json encontrado na pasta de entrada.")
        return

    # Etapa 1: Coletar todos os mapeamentos IP -> Hostname
    for filename in lista_arquivos:
        filepath = os.path.join(PASTA_INPUT_RAW, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                dados_traces = json.load(f)
            except json.JSONDecodeError:
                print(f"  [AVISO] Arquivo JSON inválido, pulando: {filename}")
                continue
            
            for trace in dados_traces:
                for hop in trace.get('val', []):
                    ip = hop.get('ip')
                    hostname = hop.get('hostname')
                    
                    # Só nos importamos com os casos onde ambos existem
                    if ip and hostname:
                        ip_para_hostnames[ip].add(hostname)

    print("📊 Mapeamento de IPs e Hostnames concluído. Procurando por conflitos...")

    # Etapa 2: Filtrar apenas os IPs com mais de um hostname (conflitos)
    ips_conflitantes = {
        ip: hostnames
        for ip, hostnames in ip_para_hostnames.items()
        if len(hostnames) > 1
    }
    
    if not ips_conflitantes:
        print("✅ Ótima notícia! Nenhum conflito de IP com múltiplos hostnames foi encontrado.")
        # Cria um arquivo vazio com cabeçalho para indicar que o script rodou
        with open(ARQUIVO_SAIDA_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ip', 'hostname_1', 'hostname_2'])
        return

    print(f"🚨 Encontrados {len(ips_conflitantes)} IPs com múltiplos nomes associados.")

    # Etapa 3: Salvar os pares de conflitos no arquivo CSV
    with open(ARQUIVO_SAIDA_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ip', 'hostname_1', 'hostname_2'])
        
        total_pares_conflitantes = 0
        for ip, hostnames in ips_conflitantes.items():
            # Gera todas as combinações de pares únicos de hostnames para o IP
            for par_de_nomes in itertools.combinations(sorted(list(hostnames)), 2):
                writer.writerow([ip, par_de_nomes[0], par_de_nomes[1]])
                total_pares_conflitantes += 1

    print(f"✅ Conflitos salvos com sucesso em '{ARQUIVO_SAIDA_CSV}'.")
    print(f"   -> Total de {total_pares_conflitantes} pares de nomes conflitantes foram registrados.")
    print("--- SCRIPT FINALIZADO ---")


if __name__ == '__main__':
    identificar_conflitos_ip_hostname()