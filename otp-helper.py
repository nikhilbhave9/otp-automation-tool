import imaplib
import email
import time
import os
import re
import requests

from email.header import decode_header
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager



load_dotenv()

# STATIC - Gmail credentials that all OTPs from all platforms will be forwarded to
GMAIL_USER = os.getenv('RECEIVER_EMAIL')
GMAIL_PASSWORD = os.getenv('RECEIVER_PASSWORD')

# DYNAMIC - Can be made dynamic by using a config file for different platforms
OTP_EMAIL_SUBJECT = "Your OTP Code" 
WEBSITE_URL = "http://localhost:8000/verify-otp" # being used for making a post request, not an actual webpage

def get_latest_otp():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASSWORD)

        mail.select("inbox")
        status, messages = mail.search(None, '(SUBJECT "Your OTP Code")')
        messages = messages[0].split()
        if not messages:
            print("No OTP email found.")
            return None
        latest_email_id = messages[-1]
        status, msg_data = mail.fetch(latest_email_id, "(RFC822)")
        
        if status != "OK":
            print("Failed to fetch email.")
            return None
        
        # Parse the email content
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Check if the email is multipart
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        # Skip attachments
                        if "attachment" in content_disposition:
                            continue
                        
                        # Get the email body
                        try:
                            payload = part.get_payload(decode=True)
                            if payload is not None:
                                body = payload.decode()
                                if content_type == "text/plain":
                                    otp = re.findall(r'\b\d{6}\b', body)
                                    if otp:
                                        mail.store(latest_email_id, '+FLAGS', '\\Seen')
                                        return otp[0]
                        except Exception as e:
                            print(f"Error decoding email part: {e}")
                else:
                    # Non-multipart email
                    try:
                        body = msg.get_payload(decode=True).decode()
                    except Exception as e:
                        print(f"Error decoding email payload: {e}")
                        continue
                    
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

def submit_otp(email, otp):

    # # API method (Selenium can also be used)
    # data = {
    #     "email": email,
    #     "otp": otp
    # }

    # time.sleep(4)
    
    # response = requests.post(WEBSITE_URL, data=data)
    # if response.status_code == 200:
    #     print("OTP submitted successfully.")
    # else:
    #     print("Failed to submit OTP. Status code:", response.status_code)

    # Selenium method (API can also be used)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode if needed
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")

    # Initialize the Chrome driver
    driver = webdriver.Chrome(executable_path='/usr/bin/chromedriver', options=chrome_options, service_args=['--verbose', '--log-path=/tmp/chromedriver.log'])

    try:
        # Open the OTP page (assuming you have the local URL or a specific endpoint)
        driver.get("http://localhost:8000/otp?email=" + email) # Can be made dynamic
        
        # Wait for the page to load
        time.sleep(2)

        # Find the OTP input field and enter the OTP
        otp_input = driver.find_element(By.ID, "otp")
        otp_input.send_keys(otp)

        # Submit the form
        form = driver.find_element(By.TAG_NAME, "form")
        form.submit()

        # Optional: Wait and print the result
        time.sleep(2)
        print("OTP submitted successfully.")
    except Exception as e:
        print(f"Failed to submit OTP: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    otp = get_latest_otp()
    if otp:
        print("OTP:", otp)
        email = input("Enter your email: ")
        submit_otp(email, otp)
    else:
        print("No OTP retrieved.")
