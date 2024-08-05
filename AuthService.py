import csv
import random
import os
import smtplib
import secrets
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException

class AuthService():
    def __init__(self):
        # Can be replaces with a secure database connection where all the users are stored
        self.users_file_path = "users.csv"
        self.otp_file_path = "otps.csv"
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_APP_PASSWORD')

    def read_users_from_csv(self) -> dict:
        users = {}
        with open(self.users_file_path, mode='r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                users[row['email']] = row['password']
        return users
    
    def authenticate_user(self, email, password):
        users_db = self.read_users_from_csv()
        if email not in users_db or users_db[email] != password:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    
    def handle_stale_otp(self, email):
        otp_exists = False
        with open(self.otp_file_path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == email:
                    otp_exists = True
                    break
        if otp_exists:
            self.delete_otp(email)
            print("Stale OTP deleted")
        else:
            print("No stale OTP found")
            
    def generate_otp(self) -> str:
        return str(random.randint(100000, 999999))
        
    def save_otp_to_file(self, email, otp):
        # Can be replaced with a secure database connection/secrets manager
        with open(self.otp_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([email, otp])

    def get_otp_from_file(self, email):
        with open(self.otp_file_path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] == email:
                    return row[1]
        print("No OTP found for this email")
        return None

    def send_otp_to_email(self, email, otp):
        sender_email = self.sender_email
        sender_password = self.sender_password
        message = MIMEMultipart("alternative") # Can be plain OR html
        message["Subject"] = "Your OTP Code"
        message["From"] = sender_email
        message["To"] = email

        text = f"Your OTP code is {otp}"
        part = MIMEText(text, "plain")
        message.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message.as_string())

    def delete_otp(self, email):
        # Read all lines except the ones to delete
        lines = []
        with open(self.otp_file_path, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row[0] != email:
                    lines.append(row)

        # Write the remaining lines back to the file
        with open(self.otp_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(lines)

    def verify_otp(self, email, otp):
        stored_otp = self.get_otp_from_file(email)
        if stored_otp == otp:
            self.delete_otp(email)
            return True
        else:
            print("Invalid OTP")
            return False
        
    def generate_dummy_token(self):
        return secrets.token_hex(16)