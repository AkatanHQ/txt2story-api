# app/database/database.py
import os
from psycopg2 import pool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

# Initialize a connection pool
db_pool = pool.SimpleConnectionPool(
    1, 20, DATABASE_URL  # 1 min connection, 20 max connections
)

# Dependency to provide a database connection for each request
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    finally:
        db_pool.putconn(conn)
