from pydantic import BaseModel, Field
from typing import Optional


class Product(BaseModel):
    product_id: str
    product_name: str
    category: str
    brand: str
    description: str
    current_price: float
    cost: float
    stock_quantity: int
    monthly_sales: int
    average_rating: float
    review_count: int
    supplier: str
    last_updated: str


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    answer: str
    tools_used: list[str]
    reasoning: str
    query_id: Optional[int] = None
