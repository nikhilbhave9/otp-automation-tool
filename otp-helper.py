import imaplib
import email
from email.header import decode_header
import re
import time
import os
import requests
import sys
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display

# os.environ['PYVIRTUALDISPLAY_DISPLAYFD'] = '0'

load_dotenv()

# Developer credentials
# (These credentials will receive the OTP)
DEV_USER = os.getenv('DEVELOPER_EMAIL')
DEV_PASSWORD = os.getenv('DEVELOPER_PASSWORD')

# Actual user credentials
# (These credentials will be used to simulate sign-in)
USER_EMAIL = os.getenv('USER_EMAIL')
USER_PASSWORD = os.getenv('USER_PASSWORD')

BASE_URL = "http://webapp:8001" # To be made dynamic with the required dashboard URl

def get_latest_otp():
    try:
        # Mailserver connection
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(DEV_USER, DEV_PASSWORD)
        mail.select("inbox")

        # Search email with a specific subject
        status, data = mail.search(None, '(SUBJECT "Your OTP Code")') # Can be made dynamic based on a config file
        if status != 'OK':
            print("Error searching for emails.")
            return None

        # Get email ids
        email_ids = data[0].split()
        if not email_ids:
            print("No OTP email found.")
            return None

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        if status != 'OK':
            print("Error fetching required email.")
            return None
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Extract the email body
                body = None
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()
                
                if body:
                    otp = re.findall(r'\b\d{6}\b', body) # Can be made dynamic based on a config file
                    if otp:
                        # Mark the email as read
                        mail.store(latest_email_id, '+FLAGS', '\\Seen')
                        return otp[0]
                    else:
                        print("OTP not found in the email body.")
                else:
                    print("Failed to extract the email body.")
            else:
                print("Incomplete email data.")
        
        print("OTP not found in the email.")
        return None
        
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        mail.logout()


def perform_login():

    # USE SELENIUM METHOD

    # # # Start virtual display
    # display = Display(visible=0, size=(1400, 900))
    # display.start()

    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Remote(
        command_executor='http://selenium:4444/wd/hub',
        options=chrome_options
    )

    import ipdb; ipdb.set_trace()
    driver.get(f"{BASE_URL}/")
    driver.find_element(By.ID, "email").send_keys(USER_EMAIL)
    driver.find_element(By.ID, "password").send_keys(USER_PASSWORD)
    driver.find_element(By.XPATH, '//form[@method="post" and @action="/sign-in"]//button[@type="submit" and @class="btn"]').click()
    time.sleep(5)

    otp = get_latest_otp()
    if not otp:
        print("Error, No valid OTP  or OTP email found. Exiting")
        return
    print(f"OTP: {otp}") # For debugging, delete later

    driver.find_element(By.ID, "otp").send_keys(otp)
    driver.find_element(By.XPATH, '//form[@method="post" and @action="/verify-otp"]//button[@type="submit" and @class="btn"]').click()

    time.sleep(5)

    print(driver.current_url)
    if "success" in driver.current_url:
        print("Sign-in successful.")
    else:
        print("Failed to sign in. Exiting")
        return

    # USE API METHOD 
    # (we can alternatively use selenium to simulate the login process)

    # Hit the sign-in endpoint with the user credentials

    # data = {
    #     "email": USER_EMAIL,
    #     "password": USER_PASSWORD
    # }
    # response = requests.post(f"{BASE_URL}/sign-in", data=data)

    # if response.status_code != 200:
    #     print("Failed to sign in.")
    #     sys.exit(1)
    # else:
    #     print("Sign-in successful.")

    # # Needs some time to receive the OTP email - adding implicit wait for now, can be replaced with explicit/fluent wait
    # time.sleep(5)

    # otp = get_latest_otp()
    # if not otp:
    #     print("No OTP found. Exiting...")
    #     return
    # print(f"OTP: {otp}")
    
    # # Make a post request to the /verify-otp endpoint
    # # with the email and OTP
    # # Use the requests library to make the request
    # data = {
    #     "email": USER_EMAIL,
    #     "otp": otp
    # }

    # response = requests.post(f"{BASE_URL}/verify-otp", data=data)

    # if response.status_code == 200:
    #     print("OTP verified successfully.")
    #     print(response.json())
    # else:
    #     print("Failed to verify OTP.")
    #     print(response.json())


if __name__ == "__main__":
    perform_login()


# docker exec -it --rm --name  otpmate_replica_gobblecube-webapp
# docker exec -it otpmate_replica_gobblecube-webapp-1 /bin/bash
# python otp-helper.py