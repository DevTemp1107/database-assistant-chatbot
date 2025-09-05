from azure.ai.projects import AIProjectClient
# from azure.ai.projects.models import Agent, AgentThread, ThreadMessage, RunStatus
from azure.ai.projects.models import RunStatus
from azure.identity import DefaultAzureCredential
from typing import Dict, Any, Optional, List
import json
import time
import logging

class AzureAgentManager:
    """Manages Azure AI agents and their interactions"""
    
    def __init__(self, config: AzureConfig, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Initialize Azure AI Project Client
        self.project_client = AIProjectClient.from_connection_string(
            conn_str=config.project_connection_string,
            credential=DefaultAzureCredential()
        )
        
        self.master_agent = None
        self.query_agent = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize and retrieve agents from Azure"""
        try:
            # Get all agents
            agents = self.project_client.agents.list_agents()
            
            # Find master and query agents by name
            for agent in agents.data:
                if agent.name == self.config.master_agent_name:
                    self.master_agent = agent
                elif agent.name == self.config.query_agent_name:
                    self.query_agent = agent
            
            if not self.master_agent:
                raise ValueError(f"Master agent '{self.config.master_agent_name}' not found")
            if not self.query_agent:
                raise ValueError(f"Query agent '{self.config.query_agent_name}' not found")
                
            self.logger.info("Successfully initialized Azure agents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def db_call(self, query: str) -> Dict[str, Any]:
        """
        Tool function for database calls
        
        Args:
            query: SQL query to execute
            
        Returns:
            Database execution results
        """
        self.logger.info(f"Executing database query: {query[:100]}...")
        return self.db_manager.execute_query(query)
    
    def _register_tools(self):
        """Register tool functions with the master agent"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "db_call",
                    "description": "Execute SQL queries on the PostgreSQL database",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The SQL query to execute"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        return tools
    
    def _handle_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Handle tool calls from the agent"""
        tool_outputs = []
        
        for tool_call in tool_calls:
            if tool_call.function.name == "db_call":
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
                query = args.get("query", "")
                
                # Execute database call
                result = self.db_call(query)
                
                # Format result for agent
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(result)
                })
        
        return tool_outputs
    
    def chat_with_master_agent(self, user_message: str) -> str:
        """
        Send message to master agent and get response
        
        Args:
            user_message: User's input message
            
        Returns:
            Agent's response as string
        """
        try:
            # Create a new thread
            thread = self.project_client.agents.create_thread()
            
            # Add user message to thread
            self.project_client.agents.create_message(
                thread_id=thread.id,
                role="user",
                content=user_message
            )
            
            # Create and run with tools
            tools = self._register_tools()
            run = self.project_client.agents.create_run(
                thread_id=thread.id,
                assistant_id=self.master_agent.id,
                tools=tools
            )
            
            # Wait for run completion and handle tool calls
            while run.status in [RunStatus.QUEUED, RunStatus.IN_PROGRESS, RunStatus.REQUIRES_ACTION]:
                time.sleep(1)
                run = self.project_client.agents.get_run(thread_id=thread.id, run_id=run.id)
                
                if run.status == RunStatus.REQUIRES_ACTION:
                    tool_calls = run.required_action.submit_tool_outputs.tool_calls
                    tool_outputs = self._handle_tool_calls(tool_calls)
                    
                    # Submit tool outputs
                    run = self.project_client.agents.submit_tool_outputs_to_run(
                        thread_id=thread.id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
            
            if run.status == RunStatus.COMPLETED:
                # Get messages from thread
                messages = self.project_client.agents.list_messages(thread_id=thread.id)
                
                # Get the latest assistant message
                for message in messages.data:
                    if message.role == "assistant":
                        return message.content[0].text.value
                        
                return "No response received from agent"
            else:
                return f"Run failed with status: {run.status}"
                
        except Exception as e:
            self.logger.error(f"Error in chat with master agent: {e}")
            return f"Error: {str(e)}"