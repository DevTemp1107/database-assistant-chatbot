import streamlit as st
import logging
from dotenv import load_dotenv
import os
from config import AzureConfig
from database_manager import DatabaseManager
from azure_agent_manager import AzureAgentManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

class ChatbotApp:
    """Main Streamlit chatbot application"""
    
    def __init__(self):
        self.config = None
        self.db_manager = None
        self.agent_manager = None
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize the application components"""
        try:
            # Load configuration
            self.config = AzureConfig.from_env()
            
            # Initialize database manager
            self.db_manager = DatabaseManager(self.config.get_db_connection_string())
            
            # Initialize agent manager
            self.agent_manager = AzureAgentManager(self.config, self.db_manager)
            
        except Exception as e:
            st.error(f"Failed to initialize application: {e}")
            st.stop()
    
    def _setup_page_config(self):
        """Configure Streamlit page settings"""
        st.set_page_config(
            page_title="Real Estate Query Assistant",
            page_icon="🏠",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def _render_sidebar(self):
        """Render sidebar with application info"""
        with st.sidebar:
            st.title("🏠 Real Estate DB Assistant")
            st.markdown("---")
            
            st.subheader("ℹ️ About")
            st.info(
                "This chatbot helps you query the real estate database using natural language. "
                "Ask questions about properties, users, locations, and sales data."
            )
            
            st.subheader("💡 Example Queries")
            examples = [
                "List all properties in California",
                "Show me properties owned by John Doe",
                "Find all sales above $500,000",
                "Update contact info for user Jane Smith",
                "Properties with more than 2000 sqft"
            ]
            
            for example in examples:
                if st.button(example, key=f"example_{hash(example)}"):
                    st.session_state.user_input = example
                    st.rerun()
    
    def _initialize_session_state(self):
        """Initialize session state variables"""
        if "messages" not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hello! I'm your Real Estate Database Assistant. I can help you query property data, user information, sales records, and more. What would you like to know?"
                }
            ]
        
        if "user_input" not in st.session_state:
            st.session_state.user_input = ""
    
    def _render_chat_interface(self):
        """Render the main chat interface"""
        st.title("💬 Chat with Real Estate Database")
        
        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask me about properties, users, sales, or locations..."):
            self._handle_user_input(prompt)
        
        # Handle sidebar example selection
        if st.session_state.user_input:
            self._handle_user_input(st.session_state.user_input)
            st.session_state.user_input = ""
    
    def _handle_user_input(self, user_input: str):
        """Handle user input and generate response"""
        # Add user message to chat
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = self.agent_manager.chat_with_master_agent(user_input)
                    st.markdown(response)
                    
                    # Add assistant message to chat history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response
                    })
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    def run(self):
        """Run the Streamlit application"""
        self._setup_page_config()
        self._initialize_session_state()
        self._render_sidebar()
        self._render_chat_interface()
