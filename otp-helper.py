import imaplib
import email
from email.header import decode_header
import re
import time
import os
import requests
import sys
from dotenv import load_dotenv


load_dotenv()

# Developer credentials
# (These credentials will receive the OTP)
DEV_USER = os.getenv('DEVELOPER_EMAIL')
DEV_PASSWORD = os.getenv('DEVELOPER_PASSWORD')

# Actual user credentials
# (These credentials will be used to simulate sign-in)
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')

BASE_URL = "http://localhost:8000" # To be made dynamic with the required dashboard URl

def get_latest_otp():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(DEV_USER, DEV_PASSWORD)
        mail.select("inbox")
        status, messages = mail.search(None, '(SUBJECT "Your OTP Code")')
        messages = messages[0].split()
        if not messages:
            print("No OTP email found.")
            return None
        latest_email_id = messages[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            otp = re.findall(r'\b\d{6}\b', body)
                            if otp:
                                mail.store(latest_email_id, '+FLAGS', '\\Seen')
                                return otp[0]
                else:
                    body = msg.get_payload(decode=True).decode()
                    otp = re.findall(r'\b\d{6}\b', body)
                    if otp:
                        mail.store(latest_email_id, '+FLAGS', '\\Seen')
                        return otp[0]
        print("OTP not found in the email.")
        return None
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def perform_login():
    
    # USE API METHOD 
    # (we can alternatively use selenium to simulate the login process)

    # Hit the sign-in endpoint with the user credentials

    data = {
        "email": USER_EMAIL,
        "password": USER_PASSWORD
    }
    response = requests.post(f"{BASE_URL}/sign-in", data=data)

    if response.status_code != 200:
        print("Failed to sign in.")
        sys.exit(1)
    else:
        print("Sign-in successful.")

    # Needs some time to receive the OTP email - adding implicit wait for now, can be replaced with explicit/fluent wait
    time.sleep(5)

    otp = get_latest_otp()
    if not otp:
        print("No OTP found. Exiting...")
        return
    print(f"OTP: {otp}")
    
    # Make a post request to the /verify-otp endpoint
    # with the email and OTP
    # Use the requests library to make the request
    data = {
        "email": USER_EMAIL,
        "otp": otp
    }

    response = requests.post(f"{BASE_URL}/verify-otp", data=data)

    if response.status_code == 200:
        print("OTP verified successfully.")
        print(response.json())
    else:
        print("Failed to verify OTP.")
        print(response.json())


if __name__ == "__main__":
    perform_login()