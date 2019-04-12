from os import environ
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

conn_string = ('mysql+pymysql://{}:{}@{}/{}?charset=utf8mb4'
               .format(environ['DB_USER'],
                       environ['DB_PASS'],
                       environ['DB_HOST'],
                       environ['DB_NAME']))

engine = create_engine(conn_string,
                       echo=False,
                       poolclass=QueuePool,
                       pool_recycle=120,
                       pool_size=5,
                       max_overflow=20)

Session = sessionmaker(bind=engine)
