"""
Strands Agents - AgentCore Memory Service
Optimized session and conversation management with DynamoDB persistence.
Integrated with Strands Agents framework for structured memory operations.
"""

import json
import logging
import os
from datetime import datetime
import boto3
from typing import Optional, List, Dict, Any

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWS Clients
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('REGION', 'us-east-1'))
memory_table = dynamodb.Table('agentcore-memory')


class AgentCoreMemory:
    """
    Strands Agents-optimized memory service.
    Manages conversation history, preferences, and session memory with dict-based output.
    """
    
    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.conversation_history: List[Dict[str, Any]] = []
        self.preferences: Dict[str, Any] = {}
        self.load_session()
    
    def load_session(self) -> None:
        """Load session from DynamoDB with error resilience."""
        try:
            logger.info(f"Loading session {self.session_id} for user {self.user_id}")
            response = memory_table.get_item(
                Key={
                    'session_id': self.session_id,
                    'user_id': self.user_id
                }
            )
            
            if 'Item' in response:
                item = response['Item']
                self.conversation_history = json.loads(item.get('conversation_history', '[]'))
                self.preferences = json.loads(item.get('preferences', '{}'))
                logger.info(f"✅ Loaded session: {len(self.conversation_history)} messages")
            else:
                logger.info(f"✅ New session initialized")
        except Exception as e:
            logger.warning(f"⚠️ Could not load session: {str(e)}")
            self.conversation_history = []
            self.preferences = {}
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add structured message to conversation history."""
        try:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            self.conversation_history.append(message)
            self.save_session()
            logger.info(f"✅ Message added - Role: {role}, Content length: {len(content)}")
            return message
        except Exception as e:
            logger.error(f"❌ Failed to add message: {str(e)}")
            raise
    
    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference with validation."""
        try:
            self.preferences[key] = value
            self.save_session()
            logger.info(f"✅ Preference set: {key}")
        except Exception as e:
            logger.error(f"❌ Failed to set preference: {str(e)}")
            raise
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference with default fallback."""
        return self.preferences.get(key, default)
    
    def save_session(self) -> None:
        """Save session to DynamoDB with structured format."""
        try:
            hist_json = json.dumps(self.conversation_history)
            pref_json = json.dumps(self.preferences)
            
            memory_table.put_item(
                Item={
                    'session_id': self.session_id,
                    'user_id': self.user_id,
                    'conversation_history': hist_json,
                    'preferences': pref_json,
                    'updated_at': datetime.now().isoformat(),
                    'TTL': int((datetime.now().timestamp())) + (24 * 3600)  # 24-hour expiry
                }
            )
            logger.info(f"✅ Session saved")
        except Exception as e:
            logger.error(f"❌ Failed to save session: {str(e)}")
            raise
    
    def get_context(self, last_n: int = 5) -> List[Dict[str, Any]]:
        """Get last N messages for agent context window."""
        context = self.conversation_history[-last_n:] if self.conversation_history else []
        logger.info(f"✅ Retrieved {len(context)} context messages")
        return context
    
    def get_full_history(self) -> List[Dict[str, Any]]:
        """Get entire conversation history."""
        logger.info(f"✅ Retrieved full history: {len(self.conversation_history)} messages")
        return self.conversation_history
    
    def clear_history(self) -> None:
        """Clear conversation history (user request)."""
        try:
            self.conversation_history = []
            self.save_session()
            logger.info(f"✅ History cleared for user {self.user_id}")
        except Exception as e:
            logger.error(f"❌ Failed to clear history: {str(e)}")
            raise
    
    def get_session_memory(self) -> Dict[str, Any]:
        """Get complete structured session memory."""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "conversation_history": self.conversation_history,
            "preferences": self.preferences,
            "updated_at": datetime.now().isoformat()
        }
