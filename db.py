# db.py
from  config import  db_config
import pymysql


def get_db_connection():

    return pymysql.connect(**db_config)