from pydantic import BaseModel,Field
from typing import List, Dict

# —— 数据模型 —— #
class LoginRequest(BaseModel):
    username: str
    password: str


class Product(BaseModel):
    id: int
    name: str

class ProductList(Product):
    cost_unit_price: float
    shipping_fee: float
    cost_tax_rate: float



# 固定费用数据结构
class FixedCost(BaseModel):
    month: str
    dept: str
    rent: float
    salary: float
    travel: float
    other: float
    marketing_share: float
    customer_service_share: float



# 请求体模型
class ProductAdd(BaseModel):
    name: str
    cost_unit_price: float
    shipping_fee: float
    cost_tax_rate: float

class ProductInput(BaseModel):
    id: int
    name: str  # ✅ 新增字段
    quantity: int = Field(..., gt=0)                 # 销售数量
    unit_price: float = Field(..., ge=0)             # 含税单价
    refund_rate: float = Field(..., ge=0, le=1)       # 退款率
    sample_fee_rate: float = Field(..., ge=0, le=1)   # 寄样费用率
    influencer_rate: float = Field(..., ge=0, le=1)   # 达人佣金率
    slot_fee_rate: float = Field(..., ge=0, le=1)     # 坑位费（保GMV）率
    ad_spend_amount: float = Field(..., ge=0)         # 广告支出金额
    slot_fee_amount: float = Field(..., ge=0)         # 坑位费（不保GMV）金额
    influencer_tax_rate: float = Field(..., ge=0, le=1)  # 达人佣金税率
    slot_fee_tax_rate: float = Field(..., ge=0, le=1)    # 坑位费税率

    class Config:
        extra = "ignore"  # 忽略前端传来的额外字段

class CalculationInput(BaseModel):
    department: str
    month: str
    products: List[ProductInput]
