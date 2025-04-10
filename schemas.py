from pydantic import BaseModel
from typing import Optional


class User_add(BaseModel):
    secret: str
    passphrase: Optional[str] 
    ttl_seconds: Optional[int]

class Detail(BaseModel):
    status_code: int
    detail: str