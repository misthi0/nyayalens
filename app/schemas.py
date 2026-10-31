import re
from pydantic import BaseModel, Field, field_validator


class _Email(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", v):
            raise ValueError("Enter a valid email address")
        return v


class RegisterIn(_Email):
    name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=6, max_length=128)


class LoginIn(_Email):
    password: str
