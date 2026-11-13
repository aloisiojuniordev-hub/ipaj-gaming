"""Schemas Pydantic de entrada e saída da API."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    category: str
    price: Decimal
    description: str


class RecommendationRequest(BaseModel):
    cart: list[str] = Field(default_factory=list, max_length=50)
    limit: int = Field(default=4, ge=1, le=10)


class RecommendationOut(BaseModel):
    product: ProductOut
    confidence: float
    lift: float
    support: float
    because: list[ProductOut]
    explanation: str


class RecommendationResponse(BaseModel):
    cart: list[str]
    recommendations: list[RecommendationOut]
    message: str | None = None


class RuleOut(BaseModel):
    antecedents: list[ProductOut]
    consequents: list[ProductOut]
    support: float
    confidence: float
    lift: float
    leverage: float


class ItemsetOut(BaseModel):
    items: list[ProductOut]
    support: float


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)  # limite do bcrypt


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class OrderItemIn(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, le=20)
    from_recommendation: bool = False


class OrderIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)
    guest_label: str | None = Field(default=None, max_length=60)


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    product_id: str
    quantity: int
    unit_price: Decimal
    from_recommendation: bool


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    total: Decimal
    created_at: datetime
    is_guest: bool
    items: list[OrderItemOut]
