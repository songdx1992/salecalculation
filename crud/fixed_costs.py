from typing import List
from backend.db import get_db_connection
from backend.models import FixedCost


def get_all_fixed_costs() -> List[FixedCost]:
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT  month, dept, rent, salary, travel, other, marketing_share, customer_service_share
                FROM ods_fixed_costs
                ORDER BY month
            """
            cursor.execute(sql)
            results = cursor.fetchall()

            fixed_costs = []
            for row in results:
                fixed_costs.append({
                    "month": row["month"],
                    "dept": row["dept"],
                    "rent": float(row["rent"]),
                    "salary": float(row["salary"]),
                    "travel": float(row["travel"]),
                    "other": float(row["other"]),
                    "marketing_share": float(row["marketing_share"]),
                    "customer_service_share": float(row["customer_service_share"])
                })
            print(">>> 正在调用 /fixed_costs 接口 <<<")
            print(fixed_costs)
            return fixed_costs

    finally:
        conn.close()

def save_fixed_cost_data(data: List[FixedCost]) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
        REPLACE INTO ods_fixed_costs
        (month, dept, rent, salary, travel, other, marketing_share, customer_service_share)
        VALUES (%(month)s, %(dept)s, %(rent)s, %(salary)s, %(travel)s, %(other)s, %(marketing_share)s, %(customer_service_share)s)
    """
    try:
        for item in data:
            cursor.execute(query, item.dict())
        conn.commit()
        return {"success": True, "message": "保存成功"}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": "保存失败", "error": str(e)}
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    get_all_fixed_costs()