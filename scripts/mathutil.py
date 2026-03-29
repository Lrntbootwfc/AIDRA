import math

def calculate_shannon_entropy(probabilities):
    """
    H(T) = -sum(p(t) * log2(p(t)))
    Calculates the information density of target associations.
    """
    if not probabilities:
        return 0
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
    return entropy

def calculate_confidence_score(path_found, entropy_score, agent_consensus=True):
    """
    Enhanced Logic for AIDRA Enterprise.
    Returns a score between 0 and 1.
    """
    
    base_score = 0.65 if path_found else 0.15
    

    specificity = max(0, 1 - (entropy_score / 2.0))
    adjustment = specificity * 0.25
    
    # 3. Bonus for Agent Consensus (If all 8 agents agree)
    bonus = 0.1 if agent_consensus and path_found else 0.0
    
    final_score = round(base_score + adjustment + bonus, 2)
    
    # Ensuring it doesn't cross 1.0
    return min(final_score, 1.0)