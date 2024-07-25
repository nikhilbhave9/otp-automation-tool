import csv
import random
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CSV_FILE_PATH = 'users.csv'
OTP_STORE = {}  # Dictionary to store OTPs temporarily

app.mount("/static", StaticFiles(directory="static"), name="static")

class User(BaseModel):
    email: str
    password: str

# ====================
# Home Route 
# ====================

@app.get("/", response_class=HTMLResponse)
async def read_sign_in(request: Request):
    return templates.TemplateResponse("sign_in.html", {"request": request})

# ====================
# Sign-in functionality
# ====================

def read_users_from_csv() -> dict:
    users = {}
    with open(CSV_FILE_PATH, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            users[row['email']] = row['password']
    return users

@app.post("/sign-in", response_class=RedirectResponse)
async def sign_in(email: str = Form(...), password: str = Form(...)):
    users_db = read_users_from_csv()
    if email not in users_db or users_db[email] != password:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    otp = generate_otp()
    OTP_STORE[email] = otp
    send_otp_email(email, otp)

    return RedirectResponse(url=f"/otp/{email}", status_code=status.HTTP_303_SEE_OTHER)


# ====================
# OTP Handling
# ====================

def send_otp_email(email: str, otp: str):
    sender_email = os.getenv('SENDER_EMAIL')
    sender_password = os.getenv('SENDER_APP_PASSWORD')
    message = MIMEMultipart("alternative") # READUP ON THIS
    message["Subject"] = "Your OTP Code"
    message["From"] = sender_email
    message["To"] = email

    text = f"Your OTP code is {otp}"
    part = MIMEText(text, "plain") # READUP ON THIS
    message.attach(part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server: # READUP ON THIS
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, message.as_string())

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


app.get("/otp/{email}", response_class=HTMLResponse)
async def read_otp(request: Request, email: str):
    return templates.TemplateResponse("otp.html", {"request": request, "email": email})

@app.post("/verify-otp", response_class=HTMLResponse)
async def verify_otp(email: str = Form(...), otp: str = Form(...)):
    if OTP_STORE.get(email) == otp:
        return HTMLResponse(f"Hello {email}, OTP verified successfully!")
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")
