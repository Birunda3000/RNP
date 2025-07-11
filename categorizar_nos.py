import re
import os
from collections import Counter

# --- CONFIGURAÇÃO ---
ARQUIVO_DE_NOS = 'lista_completa_de_nos.txt'

def categorizar_nos_com_nova_regra(filepath):
    """
    Lê uma lista de hostnames e os separa em dois grupos, agora com a
    nova regra para matches múltiplos e idênticos.
    """
    if not os.path.exists(filepath):
        print(f"🚨 ERRO: Arquivo '{filepath}' não foi encontrado.")
        return

    estados_br = {
        'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
        'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
        'sp', 'se', 'to'
    }

    grupo_match_perfeito = []
    grupo_casos_complexos = []

    with open(filepath, 'r', encoding='utf-8') as f:
        hostnames = [line.strip() for line in f if line.strip()]

    print(f"--- Analisando {len(hostnames)} nós com a nova regra ---")

    for host in hostnames:
        if 'no-hostname' in host.lower() or 'gateway' in host.lower():
            grupo_casos_complexos.append(host)
            continue

        partes = re.split(r'[-._\s]', host.lower())
        candidatos = [p for p in partes if p in estados_br]

        # --- LÓGICA DE CATEGORIZAÇÃO ATUALIZADA ---
        if len(candidatos) == 1:
            # Caso 1: Match perfeito com uma única sigla.
            grupo_match_perfeito.append((host, candidatos[0].upper()))
        
        elif len(candidatos) > 1:
            # Caso 2: Múltiplos matches encontrados.
            # Verificamos se todos os matches são para o mesmo estado.
            # Se o tamanho do set dos candidatos for 1, significa que todos são iguais.
            if len(set(candidatos)) == 1:
                # NOVA REGRA: Múltiplos matches, mas todos idênticos. É um match perfeito!
                grupo_match_perfeito.append((host, candidatos[0].upper()))
            else:
                # AMBIGUIDADE: Encontramos siglas de estados diferentes (ex: 'ac' e 'ro').
                grupo_casos_complexos.append(host)
        else: # len(candidatos) == 0
            # NENHUM MATCH: A sigla está "embutida" (ex: 'mxac').
            grupo_casos_complexos.append(host)

    # --- Imprime os resultados ---
    print("\n===================================================================")
    print(f"= Grupo 1: Match Perfeito e Único ({len(grupo_match_perfeito)} nós) =")
    print("= (1 sigla de estado isolada OU múltiplas siglas idênticas) =")
    print("===================================================================")
    for host, estado in sorted(grupo_match_perfeito):
        print(f"  -> {host:<65} | Estado Deduzido: {estado}")

    print("\n===================================================================")
    print(f"= Grupo 2: Casos Complexos ou Ambíguos ({len(grupo_casos_complexos)} nós) =")
    print("= (0 ou 2+ siglas diferentes; ou siglas 'embutidas')      =")
    print("===================================================================")
    for host in sorted(grupo_casos_complexos):
        print(f"  -> {host}")

if __name__ == "__main__":
    categorizar_nos_com_nova_regra(ARQUIVO_DE_NOS)