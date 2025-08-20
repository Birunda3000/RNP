# Projeto de Mapeamento Geográfico da Rede RNP

## 1. Objetivo

Este projeto tem como objetivo analisar dados brutos de `traceroute` da Rede Nacional de Ensino e Pesquisa (RNP) para classificar geograficamente cada nó da rede, determinando o estado brasileiro ao qual pertence.

O processo é realizado através de um pipeline de scripts em Python que progressivamente extraem, analisam, refinam e validam os dados, culminando em uma visualização interativa e georreferenciada da topologia da rede sobre o mapa do Brasil.

## 2. Estrutura do Projeto

```
/
|-- data/
|   |-- raw/
|   |   |-- traceroute/
|   |       |-- monipe-ac-atraso_to_monipe-am-atraso...json
|   |       `-- ... (outros arquivos .json com dados brutos)
|   `-- processed/
|       |-- nodes.csv
|       |-- edges.csv
|       |-- ... (arquivos intermediários)
|-- 1_...py a 10_...py          <-- Scripts do pipeline de análise
|-- mapa_rede_interativo_v2.html <-- Visualização final e principal!
`-- README.md
```

## 3. Metodologia

A classificação de cada nó é realizada através de um pipeline de análise com múltiplas fases, onde cada etapa refina o resultado da anterior:

1. **Extração da Rede Base:** Os arquivos `.json` são processados para extrair uma lista única de **nós** (IPs) e **arestas** (conexões), formando a estrutura base da rede.
2. **Dedução Heurística:** Regras baseadas em padrões de nomenclatura (`hostname`) e no contexto da medição (origem/destino extraído do nome do arquivo) são aplicadas para uma dedução inicial da localização de cada nó.
3. **Consolidação por Pontuação:** Para resolver conflitos onde múltiplas regras apontam para estados diferentes, um sistema de pontuação configurável é utilizado. Ele pesa as evidências com base na confiabilidade de cada regra, elegendo o estado mais provável e marcando empates como "Ambíguos".
4. **Resolução por Topologia:** Nós ainda "Desconhecidos" ou "Ambíguos" são analisados com base em sua vizinhança na rede. Através de uma votação majoritária entre seus vizinhos diretos, o script tenta inferir a localização mais provável.
5. **Inferência Final e "Chute Educado":** Para os casos mais resistentes, uma análise de vizinhança estendida (2º grau) é realizada para forçar uma decisão ("chute"), garantindo a máxima completude dos dados. Empates nesta fase são resolvidos por ordem alfabética.
6. **Visualização:** O dataset final, é utilizado para gerar um mapa interativo, onde cada nó é posicionado geograficamente ao redor da capital do estado, permitindo a exploração visual da topologia da rede.

## 4. Como Executar o Projeto

#### Pré-requisitos

Certifique-se de ter Python 3 instalado e instale os requirements.txt

#### Fluxo de Execução

1. **Preparação:** Coloque todos os seus arquivos de dados `traceroute` (`.json`) na pasta `data/raw/traceroute/`.
2. **Execução dos Scripts:** Execute os scripts na ordem numérica para processar os dados em fases.
   **Bash**

   ```
   # Fase 1: Cria a base de nós e arestas
   python 2_criar_nodes_edges_baseado_nos_jsons.py

   # Fase 2: Aplica as regras de nomenclatura e contexto
   python 3_analisar_nos_por_regras.py

   # Fase 3: Resolve conflitos com o sistema de pontuação
   python 4_consolidar_analise.py

   # Fase 4: Tenta resolver ambiguidades com vizinhos diretos
   python 5_resolver_ambiguidades_vizinhos.py

   # (Opcional) Fase 5a: Desempate específico para nomes de link
   python 6_desempate_final.py

   # Fase 5b: Força uma decisão para todos os nós restantes
   python 7_chute_final_por_proximidade.py
   ```
3. **Geração da Visualização Final:**
   * Abra o script `9_gerar_mapa_interativo_v2.py`.
   * **Importante:** Certifique-se de que a variável `ARQUIVO_INPUT_NODES` dentro dele aponta para o seu dataset mais recente e corrigido (ex: `nodes_verificados.csv`).
   * Execute o script:

   **Bash**

   ```
   python 9_gerar_mapa_interativo_v2.py
   ```
4. **Análise:** Abra o arquivo `mapa_rede_interativo_v2.html` gerado no seu navegador para explorar a rede.

## 5. Descrição dos Arquivos Finais

* **`data/processed/nodes_verificados.csv`** : O dataset final e corrigido contendo a lista de todos os nós e sua localização geográfica determinada.
* **`data/processed/edges.csv`** : A lista de todas as conexões entre os nós, utilizada para desenhar o grafo.
* **`mapa_rede_interativo_v2.html`** : O principal resultado do projeto. Um arquivo HTML autônomo com a visualização geoespacial interativa da rede.
