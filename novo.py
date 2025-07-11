import pandas as pd
import os
import glob
import re
from collections import Counter

# --- CONFIGURAÇÃO ---
PASTA_DE_ENTRADA = 'datasets_arestas'
ARQUIVO_DE_SAIDA = 'delete.csv'

# --- FUNÇÃO DE MAPEAMENTO (PARA A REGRA 2) ---
def deduzir_estado_por_match_perfeito(hostname: str) -> str or None:
    """
    Versão específica da nossa função que só retorna um estado se encontrar
    um 'match perfeito' (uma única sigla de estado ou múltiplas siglas idênticas).
    Retorna None se o caso for complexo.
    """
    if not isinstance(hostname, str) or 'no-hostname' in hostname.lower() or 'gateway' in hostname.lower():
        return None

    estados_br = {
        'ac', 'al', 'ap', 'am', 'ba', 'ce', 'df', 'es', 'go', 'ma', 'mt', 'ms',
        'mg', 'pa', 'pb', 'pr', 'pe', 'pi', 'rj', 'rn', 'rs', 'ro', 'rr', 'sc',
        'sp', 'se', 'to'
    }
    
    partes = re.split(r'[-._\s]', hostname.lower())
    candidatos = [p for p in partes if p in estados_br]

    if len(candidatos) > 0 and len(set(candidatos)) == 1:
        # Se encontrou um ou mais candidatos, e todos são iguais, é um match perfeito.
        return candidatos[0].upper()
    
    # Se encontrou 0 candidatos ou candidatos de estados diferentes, não faz nada.
    return None

# --- FUNÇÃO PRINCIPAL DO PIPELINE ---
def executar_pipeline_completo():
    # 1. CONSOLIDAR TODOS OS ARQUIVOS
    padrao_arquivos = os.path.join(PASTA_DE_ENTRADA, 'arestas_*.csv')
    lista_de_arquivos = glob.glob(padrao_arquivos)
    if not lista_de_arquivos:
        print(f"🚨 ERRO: Nenhum arquivo encontrado em '{PASTA_DE_ENTRADA}'. Execute o coletor primeiro.")
        return

    print(f"--- 1. Consolidando {len(lista_de_arquivos)} arquivos... ---")
    lista_de_dataframes = []
    for arquivo in lista_de_arquivos:
        try:
            nome_base = os.path.basename(arquivo)
            parte_dos_estados = nome_base.split('_')[1]
            estado_origem, estado_destino = parte_dos_estados.split('-')
            
            df_temp = pd.read_csv(arquivo)
            df_temp['Estado_Origem_Viagem'] = estado_origem.upper()
            df_temp['Estado_Destino_Viagem'] = estado_destino.upper()
            lista_de_dataframes.append(df_temp)
        except Exception as e:
            print(f"  [AVISO] Falha ao processar o arquivo {arquivo}: {e}")

    df = pd.concat(lista_de_dataframes, ignore_index=True)
    print(f"✅ DataFrame consolidado com {len(df)} arestas.")

    # 2. APLICAR A REGRA DA VIAGEM (PRIMEIRO E ÚLTIMO SALTO)
    print("\n--- 2. Aplicando Regra 1: Mapeando primeiro e último salto de cada viagem... ---")
    df['Estado_Deduzido'] = None # Cria a nova coluna vazia

    # Encontra os últimos saltos
    indices_ultimos_saltos = df.groupby('Timestamp')['Hop_Number'].idxmax()
    ultimos_saltos = df.loc[indices_ultimos_saltos]

    # Cria um dicionário de mapeamento IP -> Estado
    mapa_ip_estado = {}
    for idx, linha in ultimos_saltos.iterrows():
        mapa_ip_estado[linha['Dest_IP']] = linha['Estado_Destino_Viagem']
        mapa_ip_estado[linha['Source_IP']] = linha['Estado_Destino_Viagem'] # O penúltimo nó também está no estado de destino

    # Encontra os primeiros saltos
    primeiros_saltos = df[df['Hop_Number'] == 1]
    for idx, linha in primeiros_saltos.iterrows():
        mapa_ip_estado[linha['Source_IP']] = linha['Estado_Origem_Viagem']
        mapa_ip_estado[linha['Dest_IP']] = linha['Estado_Origem_Viagem']
    
    # Aplica o mapeamento ao DataFrame principal
    df['Estado_Deduzido'] = pd.concat([df['Source_IP'].map(mapa_ip_estado), df['Dest_IP'].map(mapa_ip_estado)], axis=1).bfill(axis=1).iloc[:, 0]
    print("✅ Regra 1 aplicada.")

    # 3. APLICAR A REGRA DO MATCH PERFEITO ONDE AINDA ESTIVER VAZIO
    print("\n--- 3. Aplicando Regra 2: Match perfeito para nós restantes... ---")
    for index, row in df[df['Estado_Deduzido'].isnull()].iterrows():
        estado = deduzir_estado_por_match_perfeito(row['Source_Hostname'])
        if estado:
            df.loc[index, 'Estado_Deduzido'] = estado
    print("✅ Regra 2 aplicada.")

    # 4. SALVAR O RESULTADO
    print(f"\n--- 4. Salvando o resultado em '{ARQUIVO_DE_SAIDA}'... ---")
    df.to_csv(ARQUIVO_DE_SAIDA, index=False)
    print("✅ Arquivo salvo com sucesso.")

    # 5. ANÁLISE FINAL: VERIFICAR INCONSISTÊNCIAS DE NOMES
    print("\n--- 5. Analisando se o mesmo IP possui nomes diferentes... ---")
    
    # Junta todos os IPs e Hostnames em duas colunas para facilitar a análise
    ips = pd.concat([df['Source_IP'], df['Dest_IP']], ignore_index=True)
    hostnames = pd.concat([df['Source_Hostname'], df['Dest_Hostname']], ignore_index=True)
    df_nos = pd.DataFrame({'IP': ips, 'Hostname': hostnames}).drop_duplicates()
    
    # Agrupa por IP e conta quantos nomes únicos cada um tem
    contagem_nomes_por_ip = df_nos.groupby('IP')['Hostname'].nunique()
    
    # Filtra apenas os IPs com mais de um nome associado
    ips_inconsistentes = contagem_nomes_por_ip[contagem_nomes_por_ip > 1]

    if ips_inconsistentes.empty:
        print("✅ Análise concluída: Nenhum IP foi encontrado com múltiplos hostnames associados.")
    else:
        print(f"🚨 ALERTA: Foram encontrados {len(ips_inconsistentes)} IPs com múltiplos nomes associados!")
        for ip, contagem in ips_inconsistentes.items():
            nomes = df_nos[df_nos['IP'] == ip]['Hostname'].unique()
            print(f"\n  -> IP: {ip} está associado a {contagem} nomes:")
            for nome in nomes:
                print(f"     - {nome}")

if __name__ == "__main__":
    executar_pipeline_completo()