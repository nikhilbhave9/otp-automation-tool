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


# uvicorn main:app --reload
