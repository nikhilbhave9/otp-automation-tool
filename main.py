from fastapi import FastAPI, Form, Request, Response, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from AuthService import AuthService
   
load_dotenv()

# Initiate app + templates
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initiate AuthService
auth_service = AuthService()

# ============= ROUTING =============
# ===================================

# Home Route - redirects to sign-in page
@app.get("/", response_class=RedirectResponse)
def home_page(request: Request):
    return RedirectResponse(url="/sign-in")

# Sign-in Route
@app.get("/sign-in", response_class=HTMLResponse)
def sign_in(request: Request):
    return templates.TemplateResponse("sign_in.html", {"request": request})

# Sign-in Form Submission
@app.post("/sign-in", response_class=RedirectResponse)
def sign_in(email: str = Form(...), password: str = Form(...)):
    auth_service.authenticate_user(email, password)
    auth_service.handle_stale_otp(email)
    otp = auth_service.generate_otp()
    auth_service.save_otp_to_file(email, otp)
    auth_service.send_otp_to_email(email, otp)
    return RedirectResponse(url=f"/otp?email={email}", status_code=status.HTTP_303_SEE_OTHER)

# OTP Route
@app.get("/otp", response_class=HTMLResponse)
def otp_page(email: str, request: Request):
    return templates.TemplateResponse("otp.html", {"request": request, "email": email})

# OTP Form Submission
@app.post("/verify-otp")
async def verify_otp(request: Request, response: Response, email: str = Form(...), otp: str = Form(...)):
    stored_otp = auth_service.get_otp_from_file(email)
    if stored_otp == otp:
        auth_service.delete_otp(email)
        return RedirectResponse(url="/success", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return JSONResponse(content={"detail": "Invalid OTP"}, status_code=status.HTTP_401_UNAUTHORIZED)
    
# Success Route
@app.get("/success", response_class=HTMLResponse)
def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})
















   
# load_dotenv()

# CSV_FILE_PATH = 'users.csv'
# OTP_FILE_PATH = 'otps.csv'


# app = FastAPI()
# templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# class User(BaseModel):
#     email: str
#     password: str

# # ====================
# # Home Route 
# # ====================

# @app.get("/", response_class=HTMLResponse)
# async def read_sign_in(request: Request):
#     return templates.TemplateResponse("sign_in.html", {"request": request})

# # ====================
# # Sign-in functionality
# # ====================

# def read_users_from_csv() -> dict:
#     users = {}
#     with open(CSV_FILE_PATH, mode='r') as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             users[row['email']] = row['password']
#     return users

# # Sign-in route
# @app.post("/sign-in", response_class=RedirectResponse)
# async def sign_in(email: str = Form(...), password: str = Form(...)):

#     users_db = read_users_from_csv()
#     if email not in users_db or users_db[email] != password:
#         raise HTTPException(status_code=400, detail="Invalid username or password")
    
#     # Check if a stale OTP exists for the user and delete it
#     has_data = False
#     with open(OTP_FILE_PATH, mode='r') as file:
#         reader = csv.reader(file)
#         # Check if there is at least one row in the file
#         for _ in reader:
#             has_data = True
#             break
#     if has_data:
#         clear_otps()

#     # Generate OTP and store it temporarily
#     otp = generate_otp()
#     save_otp(email, otp)
#     # Send OTP email
#     send_otp_to_email(email, otp)

#     # Redirect to OTP input page with email as a query parameter
#     return RedirectResponse(url=f"/otp?email={email}", status_code=status.HTTP_303_SEE_OTHER)

# # ====================
# # OTP Handling
# # ====================

# def send_otp_to_email(email: str, otp: str):
#     sender_email = os.getenv('SENDER_EMAIL')
#     sender_password = os.getenv('SENDER_APP_PASSWORD')
#     message = MIMEMultipart("alternative")
#     message["Subject"] = "Your OTP Code"
#     message["From"] = sender_email
#     message["To"] = email

#     text = f"Your OTP code is {otp}"
#     part = MIMEText(text, "plain")
#     message.attach(part)

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, email, message.as_string())

# def generate_otp() -> str:
#     return str(random.randint(100000, 999999))

# def save_otp(email: str, otp: str):
#     with open(OTP_FILE_PATH, mode='a', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow([email, otp])

# def get_otp(email: str) -> Optional[str]:
#     with open(OTP_FILE_PATH, mode='r') as file:
#         reader = csv.reader(file)
#         for row in reader:
#             if row[0] == email:
#                 return row[1]
#     return None

# def delete_otp(email: str):
#     # Read all lines except the ones to delete
#     lines = []
#     with open(OTP_FILE_PATH, mode='r') as file:
#         reader = csv.reader(file)
#         for row in reader:
#             if row[0] != email:
#                 lines.append(row)

#     # Write the remaining lines back to the file
#     with open(OTP_FILE_PATH, mode='w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerows(lines)

# def clear_otps():
#     with open(OTP_FILE_PATH, mode='w', newline='') as file:
#         pass

# @app.get("/otp", response_class=HTMLResponse)
# async def read_otp(request: Request, email: str):
#     return templates.TemplateResponse("otp.html", {"request": request, "email": email})

# def generate_dummy_token():
#     return secrets.token_hex(16)  # Generates a 32-character hex token

# @app.post("/verify-otp")
# async def verify_otp(email: str = Form(...), otp: str = Form(...)):
#     stored_otp = get_otp(email)
#     if stored_otp == otp:
#         token = generate_dummy_token()
#         delete_otp(email)
#         return JSONResponse(content={"message": "OTP verified successfully", "token": token}, status_code=status.HTTP_200_OK)
#     else:
#         # Return JSON response for error
#         return JSONResponse(content={"detail": "Invalid OTP"}, status_code=status.HTTP_400_BAD_REQUEST)

# # uvicorn main:app --reload
