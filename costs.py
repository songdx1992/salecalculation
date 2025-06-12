# backend/costs.py

import pymysql
from typing import Dict

db_config = {
    'host': '125.91.113.114',
    'user': 'root',
    'password': 'Report@123',
    'database': 'sales',
    'charset': 'utf8mb4'
}


def fetch_fixed_costs() -> Dict[str, Dict[str, Dict[str, float]]]:
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    query = "SELECT * FROM ods_fixed_costs"
    cursor.execute(query)
    results = cursor.fetchall()

    data = {}

    for row in results:
        month = row["month"]
        dept = row["dept"]

        # 初始化月份键
        if month not in data:
            data[month] = {}

        # 转换数值类型（数据库部分字段为 varchar）
        data[month][dept] = {
            "rent": float(row["rent"]),
            "salary": float(row["salary"]),
            "travel": float(row["travel"]),
            "other": float(row["other"]),
            "marketing_share": float(row["marketing_share"]),
            "customer_service_share": float(row["customer_service_share"]),
        }

    cursor.close()
    connection.close()

    return data


# 程序启动时加载一次（如需实时刷新建议放入 FastAPI 的依赖中）
fixed_costs_by_dept_and_month = fetch_fixed_costs()
