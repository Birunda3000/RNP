import os
import csv
import glob

# --- CONFIGURAÇÃO ---

# 1. Coloque aqui o nome da pasta onde estão seus arquivos CSV de arestas.
#    O script vai procurar por todos os arquivos que começam com "arestas_".
PASTA_DE_ENTRADA = 'datasets_arestas' 

# 2. Nome do arquivo final que conterá todos os dados consolidados.
ARQUIVO_DE_SAIDA = 'banco_de_dados_de_arestas.csv'

def consolidar_arquivos():
    """
    Lê todos os arquivos CSV de arestas na pasta de entrada, adiciona colunas de
    origem e destino da viagem (extraídas do nome do arquivo) e
    junta tudo em um único arquivo CSV mestre.
    """
    PASTA_DE_ENTRADA = 'datasets_arestas'
    ARQUIVO_DE_SAIDA = 'banco_de_dados_de_arestas.csv'

    padrao_arquivos = os.path.join(PASTA_DE_ENTRADA, 'arestas_*.csv')
    lista_de_arquivos = glob.glob(padrao_arquivos)

    if not lista_de_arquivos:
        print(f"🚨 ERRO: Nenhum arquivo 'arestas_*.csv' encontrado na pasta '{PASTA_DE_ENTRADA}'.")
        return

    print(f"✅ Encontrados {len(lista_de_arquivos)} arquivos para consolidar.")

    with open(ARQUIVO_DE_SAIDA, 'w', encoding='utf-8', newline='') as f_saida:
        writer = csv.writer(f_saida)
        
        novo_cabecalho = [
            "Timestamp", "Datetime", "Hop_Number",
            "Source_IP", "Source_Hostname",
            "Dest_IP", "Dest_Hostname",
            "Estado_Origem_Viagem", "Estado_Destino_Viagem"
        ]
        writer.writerow(novo_cabecalho)
        
        for arquivo in lista_de_arquivos:
            print(f"   -> Processando arquivo: {os.path.basename(arquivo)}")
            
            try:
                nome_base = os.path.basename(arquivo)
                parte_dos_estados = nome_base.split('_')[1]
                
                # --- LINHA CORRIGIDA ---
                estado_origem, estado_destino = parte_dos_estados.split('-') # Usando a variável correta

            except (IndexError, ValueError):
                print(f"      [AVISO] Nome de arquivo fora do padrão: '{nome_base}'. Pulando.")
                continue

            with open(arquivo, 'r', encoding='utf-8') as f_entrada:
                reader = csv.reader(f_entrada)
                next(reader, None) 
                
                for linha in reader:
                    linha.append(estado_origem.upper())
                    linha.append(estado_destino.upper())
                    writer.writerow(linha)

    print(f"\n$$$ SUCESSO! Todos os dados foram consolidados em '{ARQUIVO_DE_SAIDA}' $$$")

# --- BLOCO DE EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    consolidar_arquivos()