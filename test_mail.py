import imaplib

mail = imaplib.IMAP4_SSL("imap.hostinger.com", 993)
mail.login("careers@ecstasysolutions.com", "3*IM!RAXIEK")
print("Login successful")
mail.logout()
