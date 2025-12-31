import spacy
from spacy.util import is_package
from spacy.cli import download

MODEL_NAME = "en_core_web_sm"

try:
    nlp = spacy.load(MODEL_NAME)
except OSError:
    # Download model at runtime (Streamlit-safe)
    download(MODEL_NAME)
    nlp = spacy.load(MODEL_NAME)
