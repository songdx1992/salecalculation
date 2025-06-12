from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from backend.crud.products import products_data,add_product_to_db
from backend.crud.get_user import get_user
from backend.costs import fixed_costs_by_dept_and_month
from collections import defaultdict     # 导入 defaultdict，用于汇总累加
from backend.models import LoginRequest,Product,FixedCost,ProductAdd,CalculationInput,ProductList
from backend.crud.fixed_costs import get_all_fixed_costs, save_fixed_cost_data
from typing import  Optional
from fastapi import FastAPI, Query, HTTPException,Header, Depends, APIRouter
from passlib.hash import bcrypt
from backend.utils.jwt import verify_token,create_access_token

app = FastAPI()

# 添加 CORS 中间件，允许任意来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 精确允许前端地址（推荐）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# 静态文件挂载
# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
print("路径",current_dir)
frontend_dir = os.path.join(current_dir, "../frontend")
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")



def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="认证失败")
    token = authorization.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")
    return payload["sub"]


secure_router = APIRouter(
    dependencies=[Depends(get_current_user)]
)
app.include_router(secure_router)
# —— 登录接口 —— #
@app.post("/login")
def login(req: LoginRequest):
    print(req)
    result=get_user(req.username)
    if result:
        hashed_password = result["hashed_password"]
        role = result["role"]
        # 验证密码是否匹配
        if bcrypt.verify(req.password, hashed_password):
            # 👇 成功后生成 JWT token
            access_token = create_access_token(data={"sub": req.username, "role": role})
            return {"status": "success", "username": req.username, "role": role,"token": access_token}
    raise HTTPException(status_code=401, detail="用户名或密码错误")
    # user = accounts.get(req.username)
    # if user and user["password"] == req.password:
    #     return {"status": "success", "username": req.username, "role": user["role"]}
    # raise HTTPException(status_code=401, detail="用户名或密码错误")


# —— 前端入口 —— #
# @app.get("/")
# async def read_index():
#     return FileResponse(os.path.join(frontend_dir, "index.html"))



# —— 产品列表 —— #
@secure_router.get("/products", response_model=List[Product])
def get_products():
    products = products_data()
    return [Product(id=p["id"], name=p["name"]) for p in products]

@secure_router.get("/all_products", response_model=List[ProductList])
def all_products(name: Optional[str] = Query(None, description="按名称模糊搜索")):
    products = products_data(name)
    print("all_products:",products)
    return  products


@secure_router.get("/fixed_costs", response_model=List[FixedCost])
def get_fixed_costs():
    return get_all_fixed_costs()


@secure_router.post("/save_fixed_costs")
def save_fixed_costs(data: List[FixedCost]):
    return save_fixed_cost_data(data)

@secure_router.post("/add_product")
def add_product(product: ProductAdd):
    print("add_product:",product)
    return add_product_to_db(product)


# —— 核心计算 —— #

@secure_router.post("/calculate")
def calculate(data: CalculationInput) -> Dict:

    print(">>> 收到请求")
    # 1. 读取固定费用配置
    try:

        fixed = fixed_costs_by_dept_and_month[data.month][data.department]
    except KeyError:
        raise HTTPException(status_code=400, detail="未知部门或月份配置")
    try:
        # 2. 计算所有产品的总业务 GMV（用于固定费用分摊）
        total_business_gmv = sum(p.unit_price * p.quantity for p in data.products)

        details = []
        # 汇总对象
        summary_bus: Dict[str, float] = defaultdict(float)
        summary_fin: Dict[str, float] = defaultdict(float)

        products_list = products_data()
        # print("products_list",products_list)
        for it in data.products:
            print("it单价",it.unit_price)
            # 查找产品配置
            prod = next((p for p in products_list if p["id"] == it.id), None)
            print("prod",prod)
            if not prod:
                raise HTTPException(status_code=404, detail=f"产品 ID {it.id} 未找到")

            # —— 一、业务端计算 —— #
            bus_gmv           = it.unit_price * it.quantity  # GMV = 销售数量 * 单价
            business_revenue  = bus_gmv * (1 - it.refund_rate)  # 收入总额 = GMV * (1 - 退款率)
            business_cost     = prod["cost_unit_price"] * it.quantity  # 成本总额 = 销售数量 * 单位成本
            business_gross    = business_revenue - business_cost  # 毛利额 = 收入总额 - 成本总额

            # 变动费用
            shipping_fee      = prod["shipping_fee"] * it.quantity  # 快递费 = 销售数量 * 配置运费
            sample_fee        = business_revenue * it.sample_fee_rate  # 寄样费用 = 收入总额 * 寄样比例
            platform_fee_bus  = business_revenue * 0.02  # 平台扣点 (2%) = 收入总额 * 2%
            other_pf_bus      = business_revenue * 0.01  # 平台其他费用 (1%) = 收入总额 * 1%
            influencer_fee    = business_revenue * it.influencer_rate  # 达人佣金 = 收入总额 * 佣金比例
            ad_spend          = it.ad_spend_amount  # 投流费用 = 前端填写的广告支出金额
            kol_fee           = business_revenue * 0.03  # KOL费用分摊 = 收入总额 * 3%
            slot_fee_var      = business_revenue * it.slot_fee_rate  # 坑位费(保GMV) = 收入总额 * 比例
            slot_fee_fix      = it.slot_fee_amount  # 坑位费(不保GMV) = 前端填写的具体金额

            # 固定费用分摊
            ratio             = (bus_gmv / total_business_gmv) if total_business_gmv else 0  # 分摊比例 = 产品GMV / 总GMV
            alloc_salary      = fixed["salary"] * ratio  # 分摊工资及福利
            alloc_travel      = fixed["travel"] * ratio  # 分摊差旅费
            alloc_rent        = fixed["rent"] * ratio  # 分摊租金等其他费用
            alloc_other       = fixed["other"] * ratio  # 分摊其他固定费用
            cs_alloc          = fixed["customer_service_share"]  # 客服部分摊（绝对值）
            mkt_alloc         = fixed["marketing_share"]  # 市场部分摊（绝对值）
            total_fixed       = alloc_salary + alloc_travel + alloc_rent + alloc_other + cs_alloc + mkt_alloc  # 固定费用合计

            # 计算利润
            marketing_profit_bus = business_gross - (
                shipping_fee + sample_fee + platform_fee_bus + other_pf_bus +
                influencer_fee + ad_spend + kol_fee + slot_fee_var + slot_fee_fix
            )  # 营销利润(不扣固定费用)
            sales_profit_bus     = marketing_profit_bus - total_fixed  # 销售利润(扣除固定费用)
            marketing_margin_bus = (marketing_profit_bus / business_revenue) if business_revenue else 0  # 营销利润率

            # —— 二、财务端计算 —— #
            cost_tax_rate      = prod.get("cost_tax_rate", 0.0)  # 成本单价税率
            print("成本单价",prod["cost_unit_price"])
            fin_cost_unit_price = prod["cost_unit_price"] / (1 + cost_tax_rate)  # 财务不含税成本单价 = 含税单价 / (1 + 成本单价税率)
            print("财务成本单价", fin_cost_unit_price)
            fin_unit_price     = it.unit_price/ (1 + cost_tax_rate)
            fin_gmv            = fin_unit_price * it.quantity  # 财务GMV
            fin_revenue        = fin_gmv * (1 - it.refund_rate)  # 财务收入总额
            fin_cost           = fin_cost_unit_price * it.quantity  # 财务成本总额
            fin_gross          = fin_revenue - fin_cost  # 财务毛利额

            # 财务变动费用
            shipping_fee_fin   = prod["shipping_fee"] * it.quantity / 1.06  # 财务快递费 = 业务快递费 /(1 + 6%税率)
            sample_fee_fin     = fin_revenue * it.sample_fee_rate  # 财务寄样费用
            platform_fee_fin   = platform_fee_bus / 1.06   # 财务平台扣点
            other_pf_fin       = other_pf_bus  / 1.06   # 财务平台其他费用
            influencer_fee_fin = influencer_fee/ (1 + it.influencer_tax_rate)  # 财务达人佣金
            ad_spend_fin       = it.ad_spend_amount / 1.06   # 财务投流费用
            kol_fee_fin        = kol_fee/ 1.06   # 财务KOL费用
            slot_fee_var_fin   = slot_fee_var / (1 +it.slot_fee_tax_rate)  # 财务坑位费(保GMV)
            slot_fee_fix_fin   = it.slot_fee_amount /(1 + it.slot_fee_tax_rate)  # 财务坑位费(不保GMV)

            # 财务利润

            marketing_profit_fin = fin_gross - (
                shipping_fee_fin + sample_fee_fin + platform_fee_fin + other_pf_fin +
                influencer_fee_fin + ad_spend_fin + kol_fee_fin + slot_fee_var_fin + slot_fee_fix_fin
            )  # 财务营销利润

            sales_profit_fin     = marketing_profit_fin - total_fixed  # 财务销售利润
            marketing_margin_fin = (marketing_profit_fin / fin_revenue) if fin_revenue else 0  # 财务营销利润率

            marketing_profit_slot_fee_fix = marketing_profit_fin + slot_fee_fix_fin  # 营销利润+财务坑位费(不保GMV)
            marketing_margin_slot_fee_fix_fin= (marketing_profit_slot_fee_fix/fin_revenue) if marketing_profit_slot_fee_fix else 0

            total_fixed_slot_fee_fix = total_fixed + slot_fee_fix_fin   #  固定费用+财务坑位费(不保GMV)
            # 保本分析
            breakeven_revenue_fin = (total_fixed_slot_fee_fix / marketing_margin_slot_fee_fix_fin) if marketing_margin_slot_fee_fix_fin else 0  # 财务端保本销售额
            breakeven_revenue_bus = breakeven_revenue_fin * (1 + cost_tax_rate)  # 业务端保本销售额
            breakeven_qty_bus     = (breakeven_revenue_bus / it.unit_price) if it.unit_price else 0  # 业务端保本销售数量

            # 扁平化组织输出
            bus = {
                "gmv": bus_gmv,
                "unit_cost": prod["cost_unit_price"],
                "refund_rate": it.refund_rate,
                "revenue": business_revenue,
                "cost": business_cost,
                "gross_profit": business_gross,
                "shipping_fee": shipping_fee,
                "sample_fee": sample_fee,
                "platform_fee": platform_fee_bus,
                "other_pf_fee": other_pf_bus,
                "influencer_fee": influencer_fee,
                "ad_spend": ad_spend,
                "kol_fee": kol_fee,
                "slot_fee": slot_fee_var + slot_fee_fix,
                "salary": alloc_salary,
                "travel": alloc_travel,
                "rent": alloc_rent,
                "customer_service": cs_alloc,
                "marketing": mkt_alloc,
                "roi":business_revenue/sum([influencer_fee,ad_spend,kol_fee,slot_fee_var,slot_fee_fix]),
                "marketing_profit": marketing_profit_bus,
                "sales_profit": sales_profit_bus,
                "marketing_margin": marketing_margin_bus,
                "break_even_revenue": breakeven_revenue_bus,
                "break_even_quantity": breakeven_qty_bus
            }

            fin = {
                "gmv": fin_gmv,
                "unit_cost": fin_cost_unit_price,
                "refund_rate": it.refund_rate,
                "revenue": fin_revenue,
                "cost": fin_cost,
                "gross_profit": fin_gross,
                "shipping_fee": shipping_fee_fin,
                "sample_fee": sample_fee_fin,
                "platform_fee": platform_fee_fin,
                "other_pf_fee":  other_pf_fin,
                "influencer_fee": influencer_fee_fin,
                "ad_spend": ad_spend_fin,
                "kol_fee": kol_fee_fin,
                "slot_fee": slot_fee_var_fin + slot_fee_fix_fin,
                "salary": alloc_salary,
                "travel": alloc_travel,
                "rent": alloc_rent,
                "customer_service": cs_alloc,
                "marketing": mkt_alloc,
                "roi": fin_revenue / sum([influencer_fee_fin, ad_spend_fin, kol_fee_fin,slot_fee_var_fin + slot_fee_fix_fin]),
                "marketing_profit": marketing_profit_fin,
                "sales_profit": sales_profit_fin,
                "marketing_margin": marketing_margin_fin,
                "break_even_revenue": breakeven_revenue_fin,
                "break_even_quantity": breakeven_qty_bus
            }

            # 累加到汇总
            for k, v in bus.items(): summary_bus[k] += v
            for k, v in fin.items(): summary_fin[k] += v

            details.append({"id": prod["id"], "name": prod["name"], "business": bus, "financial": fin})

        # 构建 summary
        summary = {"business": dict(summary_bus), "financial": dict(summary_fin)}

        return {"summary": summary, "details": details}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"计算出错: {str(e)}")

# 对于所有未知路径返回 index.html（支持前端路由）
@app.get("/{full_path:path}")
def spa_handler(full_path: str):
    index_path = os.path.join("frontend", "index.html")
    return FileResponse(index_path)