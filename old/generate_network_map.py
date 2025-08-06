import os
import json
import csv
from config import config

def get_estado_placeholder(hostname):
    """
    Função placeholder para determinar o estado a partir do nome do host.
    Por enquanto, retorna 'NA' como solicitado.
    """
    return 'NA'

def generate_map_files():
    """
    Processa todos os arquivos de traceroute para extrair nós e arestas da rede,
    salvando-os em nodes.csv e edges.csv.
    """
    traceroute_dir = os.path.join(config.RAW_DATA_PATH, 'traceroute')

    if not os.path.exists(traceroute_dir):
        print(f"[ERRO] O diretório de dados de traceroute não foi encontrado em: {traceroute_dir}")
        return

    print("--- Iniciando a geração do mapa da rede a partir dos dados de traceroute ---")

    nodes = {}  # Chave: identificador (hostname ou ip), Valor: {ip}
    edges = set()  # Valor: (source_identifier, target_identifier)

    # Itera sobre todos os arquivos JSON de traceroute
    for filename in os.listdir(traceroute_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(traceroute_dir, filename)
            print(f"  -> Processando arquivo: {filename}")
            
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    all_traces = json.load(f)
                except json.JSONDecodeError:
                    print(f"     [AVISO] Arquivo JSON inválido ou vazio, pulando: {filename}")
                    continue

            # Cada arquivo contém uma lista de medições de traceroute
            for trace_measurement in all_traces:
                hops = trace_measurement.get('val', [])
                if not hops:
                    continue
                
                # Itera pelos saltos para extrair nós e arestas
                for i in range(len(hops) - 1):
                    source_hop = hops[i]
                    target_hop = hops[i+1]

                    source_identifier = source_hop.get('hostname') or source_hop.get('ip')
                    target_identifier = target_hop.get('hostname') or target_hop.get('ip')
                    
                    if not source_identifier or not target_identifier or source_identifier == target_identifier:
                        continue

                    if source_identifier not in nodes:
                        nodes[source_identifier] = {'ip': source_hop.get('ip', 'N/A')}
                    if target_identifier not in nodes:
                        nodes[target_identifier] = {'ip': target_hop.get('ip', 'N/A')}

                    edge = tuple(sorted((source_identifier, target_identifier)))
                    edges.add(edge)

    print("\n--- Processamento concluído. Salvando arquivos CSV. ---")

    node_identifier_to_id = {identifier: i for i, identifier in enumerate(nodes.keys())}

    # 1. Salvar o arquivo de nós (nodes.csv)
    nodes_filepath = os.path.join(config.BASE_DIR, 'nodes.csv')
    with open(nodes_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'nome', 'ip', 'estado'])
        for identifier, node_id in node_identifier_to_id.items():
            node_info = nodes[identifier]
            ip_address = node_info['ip']
            
            # --- LÓGICA ALTERADA AQUI ---
            # Se o identificador for igual ao IP, significa que não havia hostname.
            # Nesse caso, o nome fica vazio. Caso contrário, o nome é o próprio identificador (hostname).
            nome_para_csv = '' if identifier == ip_address else identifier
            
            estado = get_estado_placeholder(identifier)
            writer.writerow([node_id, nome_para_csv, ip_address, estado])
    print(f"[SUCESSO] Arquivo de nós salvo em: {nodes_filepath} com {len(nodes)} nós.")

    # 2. Salvar o arquivo de arestas (edges.csv)
    edges_filepath = os.path.join(config.BASE_DIR, 'edges.csv')
    with open(edges_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['source', 'target'])
        for source_identifier, target_identifier in edges:
            source_id = node_identifier_to_id[source_identifier]
            target_id = node_identifier_to_id[target_identifier]
            writer.writerow([source_id, target_id])
    print(f"[SUCESSO] Arquivo de arestas salvo em: {edges_filepath} com {len(edges)} arestas.")


if __name__ == '__main__':
    generate_map_files()