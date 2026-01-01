import streamlit as st

# Load secrets from Streamlit Cloud
EMAIL_USER = st.secrets.get("EMAIL_USER", "dummy@email.com")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "dummy_password")
IMAP_SERVER = st.secrets.get("IMAP_SERVER", "imap.hostinger.com")
IMAP_PORT = int(st.secrets.get("IMAP_PORT", 993))

SUPPORTED_FILES = (".pdf", ".docx")

