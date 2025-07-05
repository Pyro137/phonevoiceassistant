# app/models/base.py
from sqlalchemy.ext.declarative import declarative_base

# Base sınıfı, tüm ORM modellerimizin türeyeceği temel sınıftır.
Base = declarative_base()