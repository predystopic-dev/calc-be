from pydantic import BaseModel

class ImageData(BaseModel):
    image: str
    dict_of_vars: dict
