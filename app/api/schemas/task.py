from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TaskBase(BaseModel):
    title: str
    description: str
    status: str = "created"


class TaskCreate(TaskBase):
    pass


class TaskFromDB(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    completed_at: Optional[datetime]


class TaskAssign(BaseModel):
    task_id: int
    user_id: int
