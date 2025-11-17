from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ProjectCreate(BaseModel):
    name: str

class Project(BaseModel):
    id: int
    name: str
    created_at: datetime
