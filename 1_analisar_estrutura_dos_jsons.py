import os
import json
from collections import defaultdict, Counter

def extrair_campos(obj, prefixo="root"):
    """
    Extrai os caminhos dos campos e seus tipos.
    Exemplo: root[0]['val'][0]['ip'] -> tipo str
    """
    campos = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            campos.update(extrair_campos(v, f"{prefixo}['{k}']"))
    elif isinstance(obj, list):
        if obj:
            # assume que todos os itens seguem a mesma estrutura
            campos.update(extrair_campos(obj[0], f"{prefixo}[0]"))
        else:
            campos[prefixo] = "list(vazia)"
    else:
        campos[prefixo] = type(obj).__name__
    return campos


def consolidar_estrutura(pasta):
    todos_campos = defaultdict(list)
    arquivos = [f for f in os.listdir(pasta) if f.endswith(".json")]

    for arq in arquivos:
        with open(os.path.join(pasta, arq), "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                campos = extrair_campos(data)
                for caminho, tipo in campos.items():
                    todos_campos[caminho].append(tipo)
            except Exception as e:
                print(f"⚠️ Erro no arquivo {arq}: {e}")

    total = len(arquivos)
    resumo = {}
    for campo, tipos in todos_campos.items():
        contagem = Counter(tipos)
        resumo[campo] = {
            "tipos": dict(contagem),
            "presenca": f"{len(tipos)}/{total}",
            "obrigatorio": len(tipos) == total
        }

    return resumo


def imprimir_resumo(resumo):
    print("📖 Estrutura consolidada dos JSONs:\n")
    for campo, info in sorted(resumo.items()):
        status = "✅ obrigatório" if info["obrigatorio"] else "⚠️ opcional"
        print(f"{campo} -> {info['tipos']} | presente em {info['presenca']} arquivos | {status}")


pasta = "data/raw/traceroute"
resumo = consolidar_estrutura(pasta)
imprimir_resumo(resumo)
