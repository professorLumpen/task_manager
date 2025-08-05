from fastapi import FastAPI

from app.core.config import settings


app = FastAPI()

if settings.DEBUG == "DEBUG":
    app.debug = True
else:
    app.debug = False
