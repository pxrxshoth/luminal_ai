from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection string
# Format: postgresql://username:password@host:port/database_name
DATABASE_URL = "postgresql://luminal:luminal@localhost:5432/luminal_db"

# Create database engine
engine = create_engine(
    DATABASE_URL,
    echo=True,  
    pool_size=5,  
    max_overflow=10  
)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


Base = declarative_base()



def get_db():
    """Creates a new database session for each request and closes it when done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()