from pydantic import BaseModel, ConfigDict


class CriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    type: str
    severity: str
    examples: list[str]
