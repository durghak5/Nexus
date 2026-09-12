# backend/test_db.py

import psycopg2
from sqlalchemy import create_engine, text
import os

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "medical_ocr",
    "user": "postgres",
    "password": "password123"
}

def test_psycopg2():
    """Test connection using psycopg2 (direct PostgreSQL driver)"""
    print("🔍 Testing connection with psycopg2...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ Connected successfully!")
        print(f"📦 PostgreSQL version: {version[0]}")
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_sqlalchemy():
    """Test connection using SQLAlchemy (ORM)"""
    print("\n🔍 Testing connection with SQLAlchemy...")
    try:
        # Create connection string
        DATABASE_URL = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        
        # Create engine
        engine = create_engine(DATABASE_URL)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.scalar()
        
        print(f"✅ Connected successfully!")
        print(f"📦 PostgreSQL version: {version}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Testing Database Connections")
    print("=" * 50)
    
    psycopg2_ok = test_psycopg2()
    sqlalchemy_ok = test_sqlalchemy()
    
    if psycopg2_ok and sqlalchemy_ok:
        print("\n🎉 All tests passed! Database is ready for use.")
    else:
        print("\n⚠️ Some tests failed. Please check your database configuration.")

