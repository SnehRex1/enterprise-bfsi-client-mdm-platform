"""
Database connection for the FastAPI application.

Authentication model:

    FastAPI
        ↓
    DefaultAzureCredential
        ↓
    Microsoft Entra access token
        ↓
    Azure SQL Database

No SQL username/password is stored in the project.
"""

import os
import struct

import pyodbc

from azure.identity import DefaultAzureCredential
from sqlalchemy import create_engine


# Microsoft ODBC constant used to pass an Entra access token
# into the SQL Server driver.
SQL_COPT_SS_ACCESS_TOKEN = 1256


def get_sql_connection():
    """
    Create one authenticated pyodbc connection.

    Azure SQL uses Microsoft Entra-only authentication,
    so the connection uses a short-lived access token.
    """

    server = os.environ["MDM_SQL_SERVER"]
    database = os.environ["MDM_SQL_DATABASE"]

    # Use the available credential chain without falling back
    # to interactive browser authentication.
    #
    # During local development, AzureCliCredential can use
    # the identity established with `az login`.
    credential = DefaultAzureCredential(
        exclude_interactive_browser_credential=True
    )

    # Request a short-lived access token specifically
    # for Azure SQL.
    token = credential.get_token(
        "https://database.windows.net/.default"
    )

    # ODBC expects the token bytes in UTF-16-LE form.
    token_bytes = token.token.encode("utf-16-le")

    # Build the access-token structure expected by
    # the Microsoft SQL Server ODBC driver.
    token_struct = struct.pack(
        f"<I{len(token_bytes)}s",
        len(token_bytes),
        token_bytes,
    )

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(
        connection_string,
        attrs_before={
            SQL_COPT_SS_ACCESS_TOKEN: token_struct
        },
    )


# SQLAlchemy gives FastAPI a reusable database engine.
#
# SQLAlchemy calls get_sql_connection() whenever a
# database connection is needed.
engine = create_engine(
    "mssql+pyodbc://",
    creator=get_sql_connection,
    pool_pre_ping=True,
    pool_recycle=300,
)
