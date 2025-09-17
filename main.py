import uvicorn
from fastapi import FastAPI

from app.api.endpoints.tasks import tasks_router
from app.api.endpoints.users import users_router
from app.api.endpoints.websocket import ws_router
from app.core.config import settings


app = FastAPI()
app.include_router(users_router)
app.include_router(tasks_router)
app.include_router(ws_router)


if settings.DEBUG:
    app.debug = True
else:
    app.debug = False


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
