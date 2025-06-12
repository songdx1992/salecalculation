from backend.db import get_db_connection
from passlib.hash import bcrypt

# 假设你想初始化账号 lmyk 密码 lmyk9999
username = "admin"
plain_password = "lmyk9999"
role="admin"



def create_user():

    # 哈希加密密码
    hashed_password = bcrypt.hash(plain_password)
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 存入数据库（示例 SQL）
            sql = """
            INSERT INTO ods_users (username, hashed_password,role)
            VALUES (%s, %s,%s)
            """
            cursor.execute(sql, (username, hashed_password,role))
            conn.commit()
    finally:
        conn.close()

if __name__ == '__main__':
    create_user()