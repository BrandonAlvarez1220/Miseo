from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base for response schemas built from ORM objects."""

    model_config = ConfigDict(from_attributes=True)
