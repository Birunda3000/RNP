# /location_deducer.py
import re

# Lista de siglas de estados para validação
STATE_ACRONYMS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO'
}

# --- Funções de Regra ---

def apply_rule1_first_hop(is_first, source_state):
    """
    Regra 1: O primeiro nó de um traceroute pertence ao estado de origem.
    Retorna uma lista com o estado de origem se for o primeiro nó.
    """
    return [source_state] if is_first and source_state else []

def apply_rule2_last_hop(is_last, dest_state):
    """
    Regra 2: O último nó de um traceroute pertence ao estado de destino.
    Retorna uma lista com o estado de destino se for o último nó.
    """
    return [dest_state] if is_last and dest_state else []

def apply_rule3_perfect_match(hostname):
    """
    Regra 3: Se uma parte do hostname corresponde perfeitamente a uma sigla de estado.
    """
    if not hostname:
        return []
    
    parts = re.split(r'[-._]', hostname.upper())
    
    # Filtra para encontrar apenas as partes que são siglas de estados válidas
    found_states = {part for part in parts if part in STATE_ACRONYMS}
    
    # A regra especifica "exatamente uma parte".
    if len(found_states) == 1:
        return list(found_states)
    
    return []

def apply_rule4_advanced_pattern_1(hostname):
    """
    Regra 4: Padrão 'monipe-[sigla_estado]-atraso.rnp.br'
    """
    if not hostname:
        return []
    
    match = re.search(r'monipe-([a-zA-Z]{2})-atraso', hostname.lower())
    if match:
        state = match.group(1).upper()
        if state in STATE_ACRONYMS:
            return [state]
            
    return []

def apply_rule5_advanced_pattern_2(hostname):
    """
    Regra 5: Padrão [prefixo][código_local][número]
    Ex: csp1 -> SP, mxac -> AC
    """
    if not hostname:
        return []
    
    # Regex para capturar padrões como cSP1, mxAC, bAC1, lanGO etc.
    # O padrão procura por um prefixo opcional, seguido por 2 letras (o estado), e talvez números/outros caracteres.
    match = re.search(r'^(?:c|cr|mx|b|lan)([a-zA-Z]{2})', hostname.lower())
    if match:
        state = match.group(1).upper()
        if state in STATE_ACRONYMS:
            return [state]
            
    return []

def apply_rule6_advanced_pattern_3(hostname):
    """
    Regra 6: Nomes que contêm 'pop-[sigla_estado]'
    Ex: rt-sc-pop-dt-sw...pop-sc.rnp.br -> SC
    """
    if not hostname:
        return []
        
    # Usa findall para capturar todas as ocorrências de pop-XX e retorna uma lista única
    matches = re.findall(r'pop-([a-zA-Z]{2})', hostname.lower())
    if matches:
        found_states = {state.upper() for state in matches if state.upper() in STATE_ACRONYMS}
        return list(found_states)
        
    return []

def apply_rule7_advanced_pattern_4(hostname):
    """
    Regra 7: Identifica nomes de parceiros ou circuitos para evitar falsos positivos.
    Esta regra, conforme a descrição, não deduz uma localização, mas ajuda a entender
    o nome do host. Para o CSV, retornaremos uma lista vazia, pois ela não aponta
    para um estado da RNP.
    """
    # Palavras-chave que indicam parceiros ou infraestrutura, não localização.
    KEYWORDS = [
        'chesf', 'furnas', 'telebras', 'claro', 'oi', 'infobarra', 'tlb',
        'brdigital', 'tisparkle', 'monet', 'amlight'
    ]
    if not hostname:
        return []

    # Se alguma palavra-chave for encontrada, esta regra não deduzirá um estado.
    if any(keyword in hostname.lower() for keyword in KEYWORDS):
        # A lógica aqui poderia ser usada para *invalidar* deduções de outras regras,
        # mas para o propósito de preencher a coluna, ela simplesmente não retorna nada.
        pass

    return []

# --- Função Agregadora ---

def deduce_location(hostname, is_first, is_last, source_state, dest_state):
    """
    Aplica todas as regras de dedução a um único nó.
    """
    return {
        'regra1': apply_rule1_first_hop(is_first, source_state),
        'regra2': apply_rule2_last_hop(is_last, dest_state),
        'regra3': apply_rule3_perfect_match(hostname),
        'regra4': apply_rule4_advanced_pattern_1(hostname),
        'regra5': apply_rule5_advanced_pattern_2(hostname),
        'regra6': apply_rule6_advanced_pattern_3(hostname),
        'regra7': apply_rule7_advanced_pattern_4(hostname),
    }