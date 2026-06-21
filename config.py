import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    _database_url = os.environ.get('DATABASE_URL')
    if _database_url and _database_url.startswith('postgres://'):
        _database_url = _database_url.replace('postgres://', 'postgresql://', 1)
    if _database_url and _database_url.startswith('postgresql://'):
        _database_url = _database_url.replace(
            'postgresql://', 'postgresql+psycopg://', 1
        )
    SQLALCHEMY_DATABASE_URI = _database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID')
    ADZUNA_API_KEY = os.environ.get('ADZUNA_API_KEY')
