from pydantic import BaseModel, EmailStr, field_serializer
from datetime import datetime, date
from typing import Optional, Any

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Account schemas
class AccountBase(BaseModel):
    name: str
    type: str

class AccountCreate(AccountBase):
    initial_balance: float = 0.0

class Account(AccountBase):
    id: int
    balance: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    amount: float
    description: Optional[str] = None
    type: str
    date: datetime
    account_id: int
    category_id: int

class TransactionCreate(BaseModel):
    amount: float
    description: Optional[str] = None
    type: str
    date: date
    account_id: int
    category_id: int

class Transaction(BaseModel):
    id: int
    user_id: int
    amount: float
    description: Optional[str] = None
    type: str
    date: datetime
    account_id: int
    category_id: int

    class Config:
        from_attributes = True

# Category schemas
class CategoryBase(BaseModel):
    name: str
    type: str

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int

    @field_serializer('type')
    def serialize_type(self, type_value):
        """Convertir enum a string"""
        if hasattr(type_value, 'value'):
            return type_value.value
        return type_value
    
    class Config:
        from_attributes = True