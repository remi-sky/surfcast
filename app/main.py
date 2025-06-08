#from dotenv import load_dotenv
#load_dotenv()

from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Surf Forecast MVP")
app.include_router(router)