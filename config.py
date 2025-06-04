import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:20522610@localhost/messangerie_app'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'