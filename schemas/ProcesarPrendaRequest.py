from pydantic import BaseModel

class ProcesarPrendaRequest(BaseModel):
    prenda_ext: str