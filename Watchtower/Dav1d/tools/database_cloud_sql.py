import os
import sqlalchemy
from google.cloud.sql.connector import Connector, IPTypes
from typing import List, Dict, Any

class CloudSQLManager:
    def __init__(self, instance_connection_name: str, db_user: str, db_pass: str, db_name: str):
        self.instance_connection_name = instance_connection_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_name = db_name
        self.connector = Connector()

    def get_connection(self):
        """Creates a connection to the Cloud SQL instance."""
        conn = self.connector.connect(
            self.instance_connection_name,
            "pg8000",
            user=self.db_user,
            password=self.db_pass,
            db=self.db_name,
            ip_type=IPTypes.PUBLIC  # Adjust if using Private IP
        )
        return conn

    def query(self, sql: str, params: dict = None) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns results as a list of dictionaries."""
        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=self.get_connection,
        )
        
        with pool.connect() as db_conn:
            result = db_conn.execute(sqlalchemy.text(sql), params or {})
            if result.returns_rows:
                keys = result.keys()
                return [dict(zip(keys, row)) for row in result.fetchall()]
            else:
                db_conn.commit()
                return [{"status": "success", "message": "Query executed successfully"}]

# Tool function wrapper
def query_cloud_sql(query: str) -> str:
    """
    Executes a SQL query against the Cloud SQL database.
    Useful for retrieving structured data, checking schemas, or managing persistent state.
    """
    # These should be in .env
    instance_name = os.getenv("CLOUD_SQL_INSTANCE")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASS")
    dbname = os.getenv("DB_NAME", "dav1d_db")
    
    if not all([instance_name, password]):
        return "Error: Cloud SQL configuration missing (CLOUD_SQL_INSTANCE, DB_PASS)."
        
    try:
        manager = CloudSQLManager(instance_name, user, password, dbname)
        results = manager.query(query)
        return str(results)
    except Exception as e:
        return f"Database Error: {str(e)}"
