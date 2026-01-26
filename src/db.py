from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from .config import DB_UID, DB_PWD, DB_SERVER, DB_DATABASE

def get_engine():
    odbc_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_DATABASE};"
        f"UID={DB_UID};"
        f"PWD={DB_PWD};"
        "TrustServerCertificate=yes;"
    )

    connection_url = URL.create(
        "mssql+pyodbc",
        query={"odbc_connect": odbc_str}
    )
    return create_engine(connection_url)
