"""
Database configuration and connection management for SQL Server
"""
import os
import pyodbc
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)


class DatabaseConfig:
    """SQL Server database configuration and connection manager"""
    
    def __init__(self):
        self.SQL_SERVER = os.getenv('SQL_SERVER')
        self.SQL_DATABASE = os.getenv('SQL_DATABASE')
        self.SQL_DRIVER = os.getenv('SQL_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.SQL_TRUSTED_CONNECTION = os.getenv('SQL_TRUSTED_CONNECTION', 'yes')
        
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self):
        """Build raw ODBC connection string"""
        if self.SQL_TRUSTED_CONNECTION.lower() == 'yes':
            return (
                f"DRIVER={{{self.SQL_DRIVER}}};"
                f"SERVER={self.SQL_SERVER};"
                f"DATABASE={self.SQL_DATABASE};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no;"
                f"MARS_Connection=yes;"
            )
        else:
            username = os.getenv('SQL_USERNAME', '')
            password = os.getenv('SQL_PASSWORD', '')
            return (
                f"DRIVER={{{self.SQL_DRIVER}}};"
                f"SERVER={self.SQL_SERVER};"
                f"DATABASE={self.SQL_DATABASE};"
                f"UID={username};"
                f"PWD={password};"
                f"Encrypt=yes;"
                f"MARS_Connection=yes;"
            )
    
    @contextmanager
    def get_connection(self):
        """Get a raw pyodbc connection"""
        conn = pyodbc.connect(self.connection_string)
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_cursor(self):
        """Get a raw pyodbc cursor"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT @@VERSION as version")
                row = cursor.fetchone()
                return {
                    "status": "success",
                    "message": "Database connection successful",
                    "server": self.SQL_SERVER,
                    "database": self.SQL_DATABASE,
                    "version": row[0] if row else "Unknown"
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database connection failed: {str(e)}",
                "server": self.SQL_SERVER,
                "database": self.SQL_DATABASE,
                "error_details": str(e)
            }
    
    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results as dicts"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def execute_non_query(self, query, params=None):
        """Execute an INSERT, UPDATE, or DELETE query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            raise Exception(f"Non-query execution failed: {str(e)}")
    
    def get_table_list(self):
        """Get list of all tables in database"""
        query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        return self.execute_query(query)
    
    def get_table_schema(self, table_name):
        """Get schema information for a specific table"""
        query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, (table_name,))


# Global instance
db = DatabaseConfig()
