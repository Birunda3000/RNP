# /data_processor.py
import json
import location_deducer as ld
from utils import get_state_from_filename

class DataProcessor:
    def __init__(self):
        self.nodes = {}  # Dicionário para armazenar nós (IP como chave)
        self.edges = set()  # Conjunto para armazenar arestas (tuplas para evitar duplicatas)
        self.next_node_id = 0

    def _get_or_create_node(self, ip, hostname=None):
        """
        Adiciona um novo nó se ele não existir ou retorna o nó existente.
        """
        if ip not in self.nodes:
            self.nodes[ip] = {
                'id': self.next_node_id,
                'ip': ip,
                'nome': set(), # Usar um set para nomes para evitar duplicatas
                'regra1': [], 'regra2': [], 'regra3': [],
                'regra4': [], 'regra5': [], 'regra6': [], 'regra7': [],
            }
            self.next_node_id += 1
        
        # Adiciona o hostname à lista de nomes do nó, se existir
        if hostname and hostname not in self.nodes[ip]['nome']:
            self.nodes[ip]['nome'].add(hostname)
        
        return self.nodes[ip]

    def process_traceroute_file(self, filepath):
        """
        Processa um único arquivo JSON de traceroute.
        """
        print(f"[PROCESSANDO] {filepath}")
        source_state, dest_state = get_state_from_filename(filepath)
        if not source_state or not dest_state:
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"[ERRO] Falha ao ler ou decodificar o arquivo {filepath}: {e}")
            return
        
        # O JSON é uma lista, então pegamos o primeiro elemento
        if not data:
            return
        trace_data = data[0].get("val", [])
        
        if not trace_data:
            return

        last_hop_ip = None
        total_hops = len(trace_data)

        for i, hop in enumerate(trace_data):
            if hop.get("success") != 1 or not hop.get("ip"):
                continue

            ip = hop["ip"]
            hostname = hop.get("hostname")
            is_first_hop = (i == 0)
            # Considera o último hop bem-sucedido
            is_last_hop = (i == total_hops - 1)

            # Cria ou obtém o nó
            node = self._get_or_create_node(ip, hostname)

            # Aplica as regras de dedução de localização
            deductions = ld.deduce_location(hostname, is_first_hop, is_last_hop, source_state, dest_state)

            # Agrega os resultados das regras (sem duplicatas)
            for rule, states in deductions.items():
                current_states = set(node[rule])
                current_states.update(states)
                node[rule] = sorted(list(current_states))

            # Adiciona a aresta (edge) se houver um nó anterior neste trace
            if last_hop_ip:
                # Garante que a aresta seja sempre (nó_menor, nó_maior) para evitar duplicatas direcionais
                edge = tuple(sorted((self.nodes[last_hop_ip]['id'], node['id'])))
                self.edges.add((edge, last_hop_ip, ip)) # Adiciona também os IPs para o CSV

            last_hop_ip = ip

    def get_nodes_as_list(self):
        """
        Converte o dicionário de nós em uma lista de dicionários para o CSV.
        """
        nodes_list = list(self.nodes.values())
        # Converte o set de nomes em uma lista ordenada para consistência
        for node in nodes_list:
            node['nome'] = sorted(list(node['nome']))
        return nodes_list

    def get_edges_as_list(self):
        """
        Converte o conjunto de arestas em uma lista de dicionários para o CSV.
        """
        return [{'source_id': edge[0][0], 'target_id': edge[0][1], 'source_ip': edge[1], 'target_ip': edge[2]} for edge in self.edges]