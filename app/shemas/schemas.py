from typing import Optional

from pydantic import BaseModel


class User_add(BaseModel):
    secret: str
    passphrase: Optional[str] 


class Detail(BaseModel):
    status_code: int
    detail: str


class Secret(BaseModel):
    secret_key: int


class Delete(Secret):
    passphrase: str
