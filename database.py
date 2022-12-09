import mysql.connector
import psycopg2
import pandas as pd
import urllib.parse
from config import get_config
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from flask_sqlalchemy import SQLAlchemy

config_data = get_config()

db = SQLAlchemy()

class Restaurent(db.Model):
    __tablename__ = "restaurent"
    __table_args__ = {'extend_existing': True} 
    id = db.Column(db.Integer, primary_key=True, nullable=False, autoincrement=True)
    RestaurentName = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    Area = db.Column(db.String(20), nullable=False)
    AddedBy =  db.Column(db.String(20), nullable=False)


def create_all_db():
    db.create_all()


def insert_row(row):
    db.session.add(row)
    db.session.flush()

def commit_session():
    db.session.commit()

def close_session():
    db.session.close()


def delete_row(rows):
    db.session.delete(rows)
    db.session.flush()

def get_engine():
    db_uri ="postgresql://{0}:{1}@{2}/{3}".format(config_data['Database_credentials']['Database_username'],config_data['Database_credentials']['Database_password'],config_data['Database_credentials']['host'],config_data['Database_credentials']['Database_name'])
    return create_engine(db_uri)


# def executequery(query):
#     try:
#         result_dataFrame = pd.read_sql(query,mydb)
#         print("result_dataFrame:",result_dataFrame)
#         mydb.close()
#         return result_dataFrame,True
#     except Exception as e:
#         mydb.close()
#         return '',False


# def insertdata(res_name):
#     sql = "insert into restaurent (RestaurentName,Location) values (%s,%s);"
#     val=(res_name,'anna nagar')
#     mydb.cursor().execute(sql,val)
#     mydb.commit()
#     return True