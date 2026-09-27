from pydantic import BaseModel, ConfigDict, EmailStr


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    category: str


class ExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    category: str


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
