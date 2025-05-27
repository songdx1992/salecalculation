# backend/costs.py
import  pymysql

fixed_costs_by_dept_and_month = {
    "202501": {
        "抖音达播-季节品": {
            "rent": 20134.20667,             # 房租费用
            "salary": 66094.46667,          # 工资及福利
            "travel": 377.636606,            # 差旅费
            "other": 4365.269548,            # 其他费用
            "marketing_share": 15175.85395,  # 市场部分摊（绝对值）
            "customer_service_share": 25144.87295  # 客服部分摊（绝对值）
        },
        "抖音自播-季节品": {
            "rent": 229.63,
            "salary": 266698.173333334,
            "travel": 431.5371187,
            "other": 10606.26836,
            "marketing_share": 20018.84423,
            "customer_service_share": 32422.42895
        },
        "小红书-季节品": {
            "rent": 0,
            "salary": 4926.538108,
            "travel": 0,
            "other": 0,
            "marketing_share": 29.01807941,
            "customer_service_share": 44.90479298
        },
        "天猫-季节品": {
            "rent": 6072.383333,
            "salary": 85233.03667,
            "travel": 2100.282184,
            "other": 3966.347674,
            "marketing_share": 24924.29594,
            "customer_service_share": 39946.08309
        },
        "京东-季节品": {
            "rent": 1216.523333,
            "salary": 41076.81667,
            "travel": 0,
            "other": 2444.326103,
            "marketing_share": 6935.437033,
            "customer_service_share": 12217.66793
        },
        "拼多多-季节品": {
            "rent": 112.39,
            "salary": 21810.94523,
            "travel": 0,
            "other": 1217.571431,
            "marketing_share": 8435.442252,
            "customer_service_share": 15258.62577
        },
        "有赞-季节品": {
            "rent": 43.22,
            "salary": 10401.106,
            "travel": 0,
            "other": 3136.472524,
            "marketing_share": 685.5234746,
            "customer_service_share": 1278.48993
        },
        "抖音达播-冰品": {
            "rent": 23779.58333,
            "salary": 60575.41333,
            "travel": 142.993394,
            "other": 2871.983785,
            "marketing_share": 9993.162759,
            "customer_service_share": 19256.66109
        },
        "抖音自播-冰品": {
            "rent": 227.32,
            "salary": 117586.8633,
            "travel": 402.8462146,
            "other": 7918.744978,
            "marketing_share": 9992.214238,
            "customer_service_share": 21443.58768
        },
        "小红书-冰品": {
            "rent": 0,
            "salary": 1740.128558,
            "travel": 0,
            "other": 0,
            "marketing_share": 6.514726127,
            "customer_service_share": 15.89349263
        },
        "天猫-冰品": {
            "rent": 3473.74,
            "salary": 51048.4,
            "travel": 1877.234483,
            "other": 3568.358993,
            "marketing_share": 14309.87605,
            "customer_service_share": 32258.69008
        },
        "京东-冰品": {
            "rent": 401.9133333,
            "salary": 14642.20333,
            "travel": 0,
            "other": 748.17723,
            "marketing_share": 1856.789233,
            "customer_service_share": 3770.006977
        },
        "拼多多-冰品": {
            "rent": 26.89333333,
            "salary": 6129.044771,
            "travel": 0,
            "other": 353.3419026,
            "marketing_share": 2099.153792,
            "customer_service_share": 3980.126277
        },
        "有赞-冰品": {
            "rent": 52.35,
            "salary": 2275.134003,
            "travel": 0,
            "other": 641.8374755,
            "marketing_share": 112.4859702,
            "customer_service_share": 238.1776486
        }
    }
}

# 数据库配置
db_config = {
    'host': '125.91.113.114',
    'user': 'root',
    'password': 'Report@123',
    'database': 'sales',
    'charset': 'utf8mb4'
}
def get_db_connection():

    return pymysql.connect(**db_config)

def get_fixed_costs():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT  month, department,rent, salary, travel, other, marketing_share, customer_service_share
                FROM ods_fixed_costs
                ORDER BY month
            """
            cursor.execute(sql)
            results = cursor.fetchall()
            print(results)

    finally:
        conn.close()
if __name__ == '__main__':
    get_fixed_costs()