# database/database.py
from databases import Database
from sqlalchemy import MetaData
from config import DATABASE_URL

database = Database(DATABASE_URL)
metadata = MetaData()
