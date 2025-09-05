import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AzureConfig:
    """Configuration class for Azure AI and database settings"""
    
    # Azure AI Configuration
    project_connection_string: str
    master_agent_name: str
    query_agent_name: str
    
    # Database Configuration
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    db_password: str
    
    @classmethod
    def from_env(cls) -> 'AzureConfig':
        """Load configuration from environment variables"""
        return cls(
            project_connection_string=os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING"),
            master_agent_name=os.getenv("MASTER_AGENT_NAME", "master-agent"),
            query_agent_name=os.getenv("QUERY_AGENT_NAME", "query-agent"),
            db_host=os.getenv("DB_HOST", "localhost"),
            db_port=os.getenv("DB_PORT", "5432"),
            db_name=os.getenv("DB_NAME"),
            db_user=os.getenv("DB_USER"),
            db_password=os.getenv("DB_PASSWORD")
        )
    
    def get_db_connection_string(self) -> str:
        """Get PostgreSQL connection string"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
