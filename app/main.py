# app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import router

#from dotenv import load_dotenv
#load_dotenv()

app = FastAPI(title="Surf Forecast MVP")

# read your front-end URL from env (set this in Railway Variables)
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")

print(f"[INFO] CORS enabled for: {FRONTEND_URL}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],  # e.g. "https://your-railway-frontend.up.railway.app"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
