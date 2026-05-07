from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PromptTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: int
    system_prompt: str
    user_template: str
    notes: str
    created_at: datetime
