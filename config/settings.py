import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER", "dummy@email.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "dummy_password")
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.hostinger.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))

SUPPORTED_FILES = (".pdf", ".docx")
