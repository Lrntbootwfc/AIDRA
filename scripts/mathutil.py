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

def calculate_confidence_score(path_found, entropy_score):
    """
    Custom logic to return a score between 0 and 1.
    """
    base_score = 0.5 if path_found else 0.1
    # Lower entropy means higher specificity (better score)
    adjustment = (1 / (1 + entropy_score)) * 0.4 
    return round(base_score + adjustment, 2)