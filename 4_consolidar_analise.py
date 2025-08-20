import pandas as pd
import os
from collections import defaultdict
import ast

# --- CONFIGURAÇÕES ---
PASTA_PROCESSED = os.path.join('data', 'processed')
ARQUIVO_INPUT_ANALISE = os.path.join(PASTA_PROCESSED, 'nodes_analisado.csv')
ARQUIVO_SAIDA_CONSOLIDADO = os.path.join(PASTA_PROCESSED, 'nodes_consolidado.csv')

# ==============================================================================
# === BLOCO DE CONFIGURAÇÃO DE PONTOS ===
# Altere os valores abaixo para ajustar o peso de cada regra na decisão final.
# ==============================================================================
CONFIGURACAO_PONTOS = {
    # PONTUAÇÃO POR CONCORDÂNCIA:
    # Um estado recebe estes pontos como bônus CADA VEZ que ele é sugerido
    # por uma regra diferente. É o indicador de confiança mais forte.
    'concordancia': 6,

    # PONTUAÇÃO POR TIPO DE REGRA:
    # Regras que usam padrões de nome muito específicos (monipe-xx, pop-xx).
    # Geralmente são muito confiáveis.
    'regra_especifica': 4,

    # Regras baseadas em nomes de link (ex: cce1-cpi1). cce1 = principal e cpi1 = secundário
    # A primeira parte do nome é considerada a "dona" da interface.
    'link_primario': 3,
    'link_secundario': 2,

    # Regras baseadas no contexto do traceroute (primeiro/último hop).
    # Como você sugeriu, podemos diminuir o peso se acharmos menos confiável.
    'contexto': 2,
}
# ==============================================================================

# Mapeia colunas para o tipo de heurística
MAPEAMENTO_HEURISTICAS = {
    "regra1: primeiro no": "contexto",
    "regra2: ultimo no": "contexto",
    "regra3: match perfeito": "regra_especifica",
    "regra4: analise avançada de string padrão 1": "regra_especifica",
    "regra5: analise avançada de string padrão 2": "link",
    "regra6: analise avançada de string padrão 3": "regra_especifica"
}

def consolidar_localizacao(row, pontos_config):
    """
    Aplica o sistema de pontuação heurístico a uma linha do dataframe
    para determinar a localização mais provável de um nó.
    """
    scores = defaultdict(int)
    justificativas = defaultdict(list)
    regras_que_apontaram = defaultdict(set)

    for coluna, tipo_heuristica in MAPEAMENTO_HEURISTICAS.items():
        try:
            estados = ast.literal_eval(row[coluna])
        except (ValueError, SyntaxError):
            estados = []
            
        if not estados:
            continue

        for i, estado in enumerate(estados):
            pontos = 0
            justificativa_regra = ""

            if tipo_heuristica == 'link':
                if i == 0:
                    pontos = pontos_config['link_primario']
                    justificativa_regra = f"Link Primário ({pontos}pts)"
                else:
                    pontos = pontos_config['link_secundario']
                    justificativa_regra = f"Link Secundário ({pontos}pts)"
            else:
                pontos = pontos_config[tipo_heuristica]
                justificativa_regra = f"{coluna.split(':')[0]} ({pontos}pts)"
            
            # Aplica bônus de concordância se o estado já foi visto por um tipo de regra diferente
            if estado in scores and tipo_heuristica not in regras_que_apontaram[estado]:
                scores[estado] += pontos_config['concordancia']
                justificativas[estado].append(f"Bônus Concordância ({pontos_config['concordancia']}pts)")
            
            scores[estado] += pontos
            justificativas[estado].append(justificativa_regra)
            regras_que_apontaram[estado].add(tipo_heuristica)
    
    if not scores:
        return "Desconhecido", "Nenhuma evidência encontrada", 0

    max_score = 0
    best_estados = []
    for estado, score in scores.items():
        if score > max_score:
            max_score = score
            best_estados = [estado]
        elif score == max_score:
            best_estados.append(estado)
    
    justificativa_str = "; ".join([f"{estado}: {score}pts ({', '.join(j)})" for estado, score, j in sorted([(s, scores[s], justificativas[s]) for s in scores], key=lambda x: -x[1])])

    if len(best_estados) > 1:
        return f"Ambíguo: {','.join(sorted(best_estados))}", justificativa_str, max_score
    else:
        return best_estados[0], justificativa_str, max_score

def executar_consolidacao():
    print("--- INICIANDO SCRIPT DE CONSOLIDAÇÃO DA ANÁLISE ---")
    if not os.path.exists(ARQUIVO_INPUT_ANALISE):
        print(f"🚨 ERRO: Arquivo de entrada '{ARQUIVO_INPUT_ANALISE}' não encontrado.")
        return

    df = pd.read_csv(ARQUIVO_INPUT_ANALISE)
    print(f"📖 Lendo {len(df)} nós para consolidar.")
    print(f"⚖️  Usando a seguinte configuração de pontos: {CONFIGURACAO_PONTOS}")

    # Aplica a função de consolidação, passando a configuração de pontos
    resultados = df.apply(lambda row: consolidar_localizacao(row, CONFIGURACAO_PONTOS), axis=1)
    df[['estado_consolidado', 'justificativa', 'confianca_score']] = pd.DataFrame(resultados.tolist(), index=df.index)

    print(f"💾 Salvando resultados em '{os.path.basename(ARQUIVO_SAIDA_CONSOLIDADO)}'...")
    cols_para_mover = ['estado_consolidado', 'confianca_score', 'justificativa', 'nome', 'ip']
    df = df[cols_para_mover + [col for col in df.columns if col not in cols_para_mover]]
    df.to_csv(ARQUIVO_SAIDA_CONSOLIDADO, index=False, encoding='utf-8')
    
    print("✅ Consolidação concluída com sucesso!")
    print("--- SCRIPT FINALIZADO ---")

if __name__ == '__main__':
    executar_consolidacao()