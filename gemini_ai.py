"""
Professional Gemini AI Integration for Discord Bot
Handles AI conversations with context and memory
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Gemini AI with fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    logger.info("✅ Gemini AI available")
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("⚠️ Gemini AI not available")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GeminiAI:
    """
    Professional Gemini AI Manager with conversation memory
    """
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = None
        self.conversations = {}  # Store conversation history
        self.max_history = 10   # Maximum messages to remember
        self.initialized = False
        
        self.initialize_gemini()
    
    def initialize_gemini(self):
        """Initialize Gemini AI connection"""
        try:
            if not GEMINI_AVAILABLE:
                logger.warning("⚠️ Gemini AI library not available")
                return False
            
            if not self.api_key:
                logger.warning("⚠️ GEMINI_API_KEY not found in environment")
                return False
            
            # Configure Gemini
            genai.configure(api_key=self.api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel('gemini-pro')
            
            # Test connection
            test_response = self.model.generate_content("Hello")
            if test_response:
                self.initialized = True
                logger.info("🎯 Gemini AI initialized successfully!")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Gemini AI: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Gemini AI is available"""
        return self.initialized and GEMINI_AVAILABLE
    
    async def generate_response(
        self, 
        user_id: int, 
        message: str, 
        context: str = "assistant",
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response with conversation memory
        
        Args:
            user_id: Discord user ID
            message: User's message
            context: Conversation context (assistant, sensei, nephew)
            system_prompt: Custom system prompt
        
        Returns:
            Dict with response data
        """
        try:
            if not self.is_available():
                return {
                    "success": False,
                    "error": "AI service not available",
                    "response": "Sorry, AI is currently unavailable."
                }
            
            # Get conversation history
            conversation_key = f"{user_id}_{context}"
            history = self.conversations.get(conversation_key, [])
            
            # Create system prompt based on context
            if not system_prompt:
                system_prompt = self._get_system_prompt(context)
            
            # Build conversation context
            conversation_context = self._build_conversation_context(
                history, message, system_prompt
            )
            
            # Generate response
            response = await self._generate_ai_response(conversation_context)
            
            if response["success"]:
                # Update conversation history
                self._update_conversation_history(
                    conversation_key, message, response["response"]
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "An error occurred while generating response."
            }
    
    def _get_system_prompt(self, context: str) -> str:
        """Get system prompt based on context"""
        prompts = {
            "assistant": """You are a helpful Discord bot assistant. You are friendly, 
                           knowledgeable, and always ready to help users with their questions. 
                           Keep responses concise but informative.""",
            
            "sensei": """You are Sensei, a wise and experienced mentor. You provide guidance, 
                        wisdom, and thoughtful advice. You speak with authority and experience, 
                        but remain approachable and caring. You often use analogies and 
                        life lessons in your responses.""",
            
            "nephew": """You are Bleky, a young and enthusiastic AI nephew. You're curious, 
                        energetic, and sometimes a bit playful. You look up to users and 
                        are eager to help and learn. You might ask follow-up questions 
                        and show genuine interest in conversations."""
        }
        
        return prompts.get(context, prompts["assistant"])
    
    def _build_conversation_context(
        self, 
        history: List[Dict], 
        current_message: str, 
        system_prompt: str
    ) -> str:
        """Build conversation context with history"""
        context_parts = [f"System: {system_prompt}\n"]
        
        # Add conversation history
        for entry in history[-self.max_history:]:
            context_parts.append(f"User: {entry['user_message']}")
            context_parts.append(f"Assistant: {entry['ai_response']}")
        
        # Add current message
        context_parts.append(f"User: {current_message}")
        context_parts.append("Assistant:")
        
        return "\n".join(context_parts)
    
    async def _generate_ai_response(self, context: str) -> Dict[str, Any]:
        """Generate AI response using Gemini"""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                self.model.generate_content, 
                context
            )
            
            if response and response.text:
                return {
                    "success": True,
                    "response": response.text.strip(),
                    "tokens_used": len(context.split())
                }
            else:
                return {
                    "success": False,
                    "error": "Empty response from AI",
                    "response": "I couldn't generate a response right now."
                }
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "Sorry, I encountered an error while thinking."
            }
    
    def _update_conversation_history(
        self, 
        conversation_key: str, 
        user_message: str, 
        ai_response: str
    ):
        """Update conversation history"""
        if conversation_key not in self.conversations:
            self.conversations[conversation_key] = []
        
        # Add new entry
        self.conversations[conversation_key].append({
            "user_message": user_message,
            "ai_response": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Limit history size
        if len(self.conversations[conversation_key]) > self.max_history:
            self.conversations[conversation_key] = \
                self.conversations[conversation_key][-self.max_history:]
    
    def clear_conversation(self, user_id: int, context: str = "assistant") -> bool:
        """Clear conversation history for a user"""
        try:
            conversation_key = f"{user_id}_{context}"
            if conversation_key in self.conversations:
                del self.conversations[conversation_key]
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def get_conversation_stats(self, user_id: int, context: str = "assistant") -> Dict[str, Any]:
        """Get conversation statistics"""
        try:
            conversation_key = f"{user_id}_{context}"
            history = self.conversations.get(conversation_key, [])
            
            return {
                "messages": len(history),
                "last_interaction": history[-1]["timestamp"] if history else None,
                "context": context
            }
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {"messages": 0, "last_interaction": None, "context": context}
    
    def get_all_conversations(self) -> Dict[str, Any]:
        """Get statistics for all conversations"""
        try:
            total_conversations = len(self.conversations)
            total_messages = sum(len(history) for history in self.conversations.values())
            
            return {
                "total_conversations": total_conversations,
                "total_messages": total_messages,
                "active_users": len(set(key.split('_')[0] for key in self.conversations.keys()))
            }
        except Exception as e:
            logger.error(f"Error getting all conversations: {e}")
            return {"total_conversations": 0, "total_messages": 0, "active_users": 0}
    
    async def generate_summary(self, text: str, max_length: int = 100) -> str:
        """Generate a summary of text"""
        try:
            if not self.is_available():
                return text[:max_length] + "..." if len(text) > max_length else text
            
            prompt = f"Summarize this text in {max_length} characters or less: {text}"
            response = await self._generate_ai_response(prompt)
            
            if response["success"]:
                return response["response"]
            else:
                return text[:max_length] + "..." if len(text) > max_length else text
                
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    def cleanup_old_conversations(self, days: int = 7):
        """Clean up conversations older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            conversations_to_remove = []
            
            for key, history in self.conversations.items():
                if history:
                    last_message_time = datetime.fromisoformat(history[-1]["timestamp"])
                    if last_message_time < cutoff_date:
                        conversations_to_remove.append(key)
            
            for key in conversations_to_remove:
                del self.conversations[key]
            
            logger.info(f"🧹 Cleaned up {len(conversations_to_remove)} old conversations")
            
        except Exception as e:
            logger.error(f"Error cleaning up conversations: {e}")

# Create global AI instance
ai = GeminiAI()

# Legacy compatibility functions
async def generate_ai_response(user_id: int, message: str, context: str = "assistant") -> str:
    """Legacy function for backward compatibility"""
    response = await ai.generate_response(user_id, message, context)
    return response.get("response", "AI is currently unavailable.")

def clear_ai_conversation(user_id: int, context: str = "assistant") -> bool:
    """Legacy function for backward compatibility"""
    return ai.clear_conversation(user_id, context)

def get_ai_instance():
    """Get AI instance"""
    return ai

# Export commonly used functions
__all__ = [
    'GeminiAI', 'ai', 'generate_ai_response', 'clear_ai_conversation', 'get_ai_instance'
]

logger.info("🎯 Gemini AI system initialized!")
logger.info(f"🤖 AI Status: {'Available' if ai.is_available() else 'Unavailable'}")
if ai.is_available():
    logger.info("🚀 Ready to handle AI conversations!")