from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    offline: bool
    project: str
