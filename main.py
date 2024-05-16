from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from app import engine

Base = declarative_base()

def create_all(engine=engine):
    Base.metadata.create_all(bind=engine)

create_all()
