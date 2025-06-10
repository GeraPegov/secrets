from pydantic import BaseModel
from typing import Optional


class User_add(BaseModel):
    secret: str
    passphrase: Optional[str] 

class Detail(BaseModel):
    status_code: int
    detail: str

class Secret(BaseModel):
    secret_key: int

class Delete(BaseModel):
    secret_key: int
    passphrase: str