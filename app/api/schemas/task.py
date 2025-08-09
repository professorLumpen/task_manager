from pydantic import BaseModel


class TaskIn(BaseModel):
    title: str
    description: str
    status: str = "created"
