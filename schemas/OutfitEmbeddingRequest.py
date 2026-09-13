from pydantic import BaseModel

class OutfitEmbeddingRequest(BaseModel):
    outfit_id: str