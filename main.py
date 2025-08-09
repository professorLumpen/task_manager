from fastapi import FastAPI

from app.api.endpoints.tasks import tasks_router
from app.api.endpoints.users import users_router
from app.core.config import settings


app = FastAPI()
app.include_router(users_router)
app.include_router(tasks_router)

if settings.DEBUG:
    app.debug = True
else:
    app.debug = False
