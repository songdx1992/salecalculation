# db.py
from  backend.config import  db_config
import pymysql
from pymysql.cursors import DictCursor


def get_db_connection():

    return pymysql.connect(
        **db_config,
        cursorclass=DictCursor)