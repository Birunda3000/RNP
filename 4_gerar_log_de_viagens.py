import os
import json
import csv

# --- CONFIGURAÇÕES ---
PASTA_INPUT_RAW = os.path.join('data', 'raw', 'traceroute')
PASTA_OUTPUT = 'output'
ARQUIVO_SAIDA_CSV = os.path.join(PASTA_OUTPUT, 'traceroute_journeys.csv')

def gerar_log_de_viagens():
    """
    Cria um log CSV onde cada linha representa um único traceroute completo,
    com sua origem, destino e a sequência de saltos formatada.
    """
    print("--- INICIANDO SCRIPT DE GERAÇÃO DO LOG DE VIAGENS DE TRACEROUTE ---")

    if not os.path.exists(PASTA_INPUT_RAW):
        print(f"🚨 ERRO: A pasta de dados brutos '{PASTA_INPUT_RAW}' não foi encontrada.")
        return

    os.makedirs(PASTA_OUTPUT, exist_ok=True)

    print(f"✍️  Gerando arquivo de saída em '{ARQUIVO_SAIDA_CSV}'...")

    # Abrimos o arquivo para escrita e já escrevemos o cabeçalho
    with open(ARQUIVO_SAIDA_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'id', 'timestamp', 'nome_arquivo_origem', 'estado_origem', 
            'estado_destino', 'sequencia_saltos'
        ])

        journey_id_counter = 1
        lista_arquivos = sorted([f for f in os.listdir(PASTA_INPUT_RAW) if f.endswith('.json')])

        print(f"🔎 Processando {len(lista_arquivos)} arquivos de dados brutos...")

        # Etapa 1: Iterar sobre cada arquivo de traceroute
        for filename in lista_arquivos:
            filepath = os.path.join(PASTA_INPUT_RAW, filename)

            # Extrai os estados da viagem a partir do nome do arquivo
            try:
                partes_nome = filename.replace('.json', '').split('_to_')
                estado_origem = partes_nome[0].split('-')[1].upper()
                estado_destino = partes_nome[1].split('-')[1].upper()
            except IndexError:
                # Se o nome do arquivo não seguir o padrão, pulamos a extração de estado
                estado_origem, estado_destino = 'N/A', 'N/A'
                print(f"  [AVISO] Não foi possível extrair estados do nome do arquivo: {filename}")

            with open(filepath, 'r', encoding='utf-8') as file_content:
                try:
                    content = file_content.read()
                    if not content: continue
                    dados_traces = json.loads(content)
                except json.JSONDecodeError:
                    continue
            
            # Etapa 2: Iterar sobre cada medição de traceroute dentro do arquivo
            for trace in dados_traces:
                timestamp = trace.get('ts')
                hops = trace.get('val', [])
                
                if not hops: continue

                # Etapa 3: Construir a string da sequência de saltos
                path_parts = []
                for hop in hops:
                    hostname = hop.get('hostname')
                    ip = hop.get('ip', 'IP_DESCONHECIDO')
                    
                    if hostname:
                        path_parts.append(hostname)
                    else:
                        # Se não houver nome, usa o IP seguido de um asterisco
                        path_parts.append(f"{ip}*")
                
                sequencia_saltos_str = " -> ".join(path_parts)
                
                # Etapa 4: Escrever a linha completa no CSV
                writer.writerow([
                    journey_id_counter,
                    timestamp,
                    filename,
                    estado_origem,
                    estado_destino,
                    sequencia_saltos_str
                ])
                
                journey_id_counter += 1

    print("\n--- SCRIPT FINALIZADO ---")
    print(f"✅ Log de viagens salvo com sucesso. Total de {journey_id_counter - 1} jornadas registradas.")

if __name__ == '__main__':
    gerar_log_de_viagens()