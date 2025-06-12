#get_user.py
from backend.db import get_db_connection

def get_user(username):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT hashed_password, role FROM ods_users WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            return   result
    finally:
        conn.close()

if __name__ == '__main__':
    print(get_user("admin"))
