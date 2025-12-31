def calculate_match(found, required, exp, min_exp):
    found = set(found)
    required = set(required)

    matched = found.intersection(required)
    missing = list(required - found)

    skill_score = (len(matched) / len(required)) * 70 if required else 0
    exp_score = 30 if exp >= min_exp else (exp / min_exp) * 30

    total_score = round(skill_score + exp_score, 2)
    return total_score, missing
