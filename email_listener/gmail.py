import imaplib
import email
import os
from email.header import decode_header
from uuid import uuid4

from config.settings import (
    EMAIL_USER,
    EMAIL_PASSWORD,
    IMAP_SERVER,
    IMAP_PORT,
    SUPPORTED_FILES
)

def fetch_resumes_from_mail(max_resumes):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    mail.select("INBOX")

    status, messages = mail.search(None, "ALL")
    email_ids = messages[0].split()

    downloaded_files = []
    emails_checked = 0

    os.makedirs("resumes", exist_ok=True)

    for email_id in reversed(email_ids):
        if len(downloaded_files) >= max_resumes:
            break

        status, msg_data = mail.fetch(email_id, "(RFC822)")
        emails_checked += 1

        for response_part in msg_data:
            if not isinstance(response_part, tuple):
                continue

            msg = email.message_from_bytes(response_part[1])

            for part in msg.walk():
                if part.get_content_disposition() != "attachment":
                    continue

                filename = part.get_filename()
                if not filename:
                    continue

                decoded_name, _ = decode_header(filename)[0]
                if isinstance(decoded_name, bytes):
                    decoded_name = decoded_name.decode(errors="ignore")

                decoded_name = decoded_name.replace("\r", "").replace("\n", "").strip()

                if not decoded_name.lower().endswith(SUPPORTED_FILES):
                    continue

                safe_name = f"{uuid4()}_{decoded_name}"
                file_path = os.path.join("resumes", safe_name)

                try:
                    with open(file_path, "wb") as f:
                        f.write(part.get_payload(decode=True))
                except Exception:
                    continue

                downloaded_files.append(file_path)

                if len(downloaded_files) >= max_resumes:
                    break

            if len(downloaded_files) >= max_resumes:
                break

    mail.logout()
    return emails_checked, downloaded_files
