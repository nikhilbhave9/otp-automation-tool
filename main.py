from fastapi import FastAPI, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

class User(BaseModel):
    name: str
    password: str

@app.get("/", response_class=HTMLResponse)
async def read_sign_in(request: Request):
    return templates.TemplateResponse("sign_in.html", {"request": request})

# ====================
# Sign-in functionality
# ====================

# @app.post("/sign-in", response_class=RedirectResponse)
# async def sign_in(username: str = Form(...), password: str = Form(...)):
#     # Here you would typically validate the user credentials
#     # For simplicity, let's assume all sign-ins are valid
#     return RedirectResponse(url="/otp", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/sign-in", response_class=RedirectResponse)
async def sign_in(name: str = Form(...), password: str = Form(...)):
    # Normally, you would validate the user credentials here.
    # For simplicity, let's assume all sign-ins are valid and redirect to greet.
    user = User(name=name, password=password)
    return RedirectResponse(url=f"/greet/{user.name}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/greet/{name}", response_class=HTMLResponse)
async def greet_user(request: Request, name: str):
    return templates.TemplateResponse("greet.html", {"request": request, "name": name})

# ====================
# OTP Handling
# ====================

@app.get("/otp", response_class=HTMLResponse)
async def read_otp(request: Request):
    return templates.TemplateResponse("otp.html", {"request": request})
