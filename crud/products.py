import os
from typing import List, Dict
import pymysql
from pymysql.cursors import DictCursor
from decimal import Decimal
from backend.db import get_db_connection
from fastapi import HTTPException
from backend.models import ProductAdd
# 静态产品列表，用于初始下拉
# products_data1= [
#     {"id": 1, "name": "猫山王榴莲冰淇淋100克", "cost_unit_price": 13.0, "shipping_fee": 7, "cost_tax_rate": 0.13},
#     {"id": 2, "name": "榴莲冰粽450克",       "cost_unit_price": 47,   "shipping_fee": 7, "cost_tax_rate": 0.13},
#     {"id": 3, "name": "六英寸榴莲蛋糕500g",  "cost_unit_price": 41.0, "shipping_fee": 7, "cost_tax_rate": 0.13},
# ]




def fetch_db_products() -> List[Dict]:
    """
    从数据库读取所有自定义产品
    返回列表，字段应包括 id, name, cost_unit_price, shipping_fee, cost_tax_rate
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT id, name, cost_unit_price, shipping_fee, cost_tax_rate FROM ods_marketingcalculation_product"
            cursor.execute(sql)
            rows = cursor.fetchall()
            # 转换Decimal为浮点数，保留两位小数
            for row in rows:
                for key in ['cost_unit_price', 'shipping_fee', 'cost_tax_rate']:
                    if key in row and isinstance(row[key], Decimal):
                        row[key] = round(float(row[key]), 2)
        return rows
    finally:
        conn.close()


def products_data() -> List[Dict]:
    """
    合并静态产品和数据库新增产品，返回总列表
    """
    db_list = fetch_db_products()
    # 合并：静态数据 + 数据库数据，若 id 冲突，可选择覆盖或跳过，此处直接拼接
    return db_list



def add_product_to_db(product: ProductAdd) -> dict:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查产品名称是否存在
            cursor.execute("SELECT COUNT(1) FROM ods_marketingcalculation_product WHERE name = %s", (product.name,))
            result = cursor.fetchone()
            if result[0] > 0:
                raise HTTPException(status_code=400, detail="产品名称已存在")

            # 插入新产品
            cursor.execute("""
                     INSERT INTO ods_marketingcalculation_product (name, cost_unit_price, shipping_fee, cost_tax_rate)
                     VALUES (%s, %s, %s, %s)
                 """, (product.name, product.cost_unit_price, product.shipping_fee, product.cost_tax_rate))
            conn.commit()
            return {"success": True, "message": "产品添加成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库错误: {str(e)}")
    finally:
        conn.close()

if __name__ == '__main__':
    products_data()



