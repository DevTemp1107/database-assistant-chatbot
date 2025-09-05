import psycopg2
import psycopg2.extras
from typing import List, Dict, Any, Optional
import logging

class DatabaseManager:
    """Handles PostgreSQL database operations"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.logger = logging.getLogger(__name__)
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query string
            
        Returns:
            Dictionary with success status, data, and error message
        """
        try:
            with psycopg2.connect(self.connection_string) as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                    cursor.execute(query)
                    
                    # Handle SELECT queries
                    if query.strip().upper().startswith('SELECT'):
                        rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description]
                        data = [dict(zip(columns, row)) for row in rows]
                        
                        return {
                            "success": True,
                            "data": data,
                            "row_count": len(data),
                            "columns": columns,
                            "error": None
                        }
                    
                    # Handle UPDATE queries
                    elif query.strip().upper().startswith('UPDATE'):
                        affected_rows = cursor.rowcount
                        conn.commit()
                        
                        return {
                            "success": True,
                            "data": None,
                            "row_count": affected_rows,
                            "columns": None,
                            "error": None,
                            "message": f"Updated {affected_rows} row(s)"
                        }
                    
                    else:
                        return {
                            "success": False,
                            "data": None,
                            "row_count": 0,
                            "columns": None,
                            "error": "Unsupported query type. Only SELECT and UPDATE are allowed."
                        }
                        
        except psycopg2.Error as e:
            self.logger.error(f"Database error: {e}")
            return {
                "success": False,
                "data": None,
                "row_count": 0,
                "columns": None,
                "error": str(e)
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "data": None,
                "row_count": 0,
                "columns": None,
                "error": f"Unexpected error: {str(e)}"
            }


if __name__=="__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_conn_string = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    testobj = DatabaseManager(db_conn_string)
    print(testobj.execute_query("select * from users"))