from pydantic import BaseModel

class ValidarOutfitRequest(BaseModel):
    prendas_ids: list[str]