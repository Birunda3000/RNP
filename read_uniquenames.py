import csv

# --- CONFIGURAÇÃO ---
# Nome do arquivo CSV que você quer analisar.
# Coloque este script e o seu arquivo CSV na mesma pasta.
NOME_DO_ARQUIVO = "datasets traceroute/traceroute esmond data ac-am 07-09-2025.csv"


def encontrar_nos_unicos(caminho_arquivo):
    """
    Lê um arquivo CSV de traceroute e retorna um set com todos os hostnames (nós) únicos.
    """
    # Usamos um 'set' para armazenar os nós. Ele automaticamente ignora itens duplicados,
    # garantindo que nossa lista final contenha apenas nomes únicos.
    nos_unicos = set()

    try:
        # Abre o arquivo CSV para leitura
        with open(caminho_arquivo, mode='r', encoding='utf-8') as f:
            # O DictReader é ideal porque nos permite acessar colunas pelo nome do cabeçalho
            leitor_csv = csv.DictReader(f)

            # Itera sobre cada linha do arquivo
            for linha in leitor_csv:
                # Pega a string completa da coluna 'HopHostnames'
                string_de_hops = linha['HopHostnames']
                
                # Divide a string em uma lista de nós individuais, usando ';' como separador
                lista_de_hops = string_de_hops.split(';')
                
                # Adiciona todos os nós encontrados nesta linha ao nosso 'set' principal.
                # O método 'update' é eficiente para adicionar todos os itens de uma lista.
                nos_unicos.update(lista_de_hops)

    except FileNotFoundError:
        print(f"🚨 ERRO: O arquivo '{caminho_arquivo}' não foi encontrado!")
        return None
    except KeyError:
        print("🚨 ERRO: O arquivo CSV não parece ter a coluna 'HopHostnames'. Verifique o cabeçalho.")
        return None
        
    return nos_unicos


# --- BLOCO DE EXECUÇÃO ---
if __name__ == "__main__":
    # Chama a função principal com o nome do arquivo configurado
    conjunto_de_nos = encontrar_nos_unicos(NOME_DO_ARQUIVO)

    # Se a função retornou os nós com sucesso, exibe os resultados
    if conjunto_de_nos:
        print(f"✅ Análise do arquivo '{NOME_DO_ARQUIVO}' concluída com sucesso!")
        print(f"🔬 Total de nós únicos encontrados: {len(conjunto_de_nos)}")
        print("-" * 40)
        
        # Imprime a lista de nós únicos em ordem alfabética para facilitar a leitura
        for no in sorted(list(conjunto_de_nos)):
            print(no)