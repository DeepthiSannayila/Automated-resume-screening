from config.settings import MIN_MATCH_SCORE

def decide(score):
    if score >= MIN_MATCH_SCORE:
        return "SHORTLISTED"
    return "REJECTED"
