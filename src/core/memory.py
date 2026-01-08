"""
Memory Management for Agents
Provides short-term (conversation) and long-term (persistent) memory
"""
from typing import List, Dict
from datetime import datetime
from .vector_store import load_vector_store
from .logger import get_logger

logger = get_logger("memory")

class ConversationMemory:
    def __init__(self, max_messages: int = 20):
        """
        Initialize conversation memory.
        """
        self.messages: List[Dict] = []
        self.max_messages = max_messages
        logger.info(f"Initialized conversation memory (max: {max_messages} messages)")
        
    def add_message(self, role: str, content: str):
        """Add message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)

        # Keep only last N messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]

        logger.debug(f"Added {role} message ({len(self.messages)} total)")
    
    def get_history(self) -> List[Dict]:
        """Get full conversation history."""
        return self.messages
    
    def get_context(self, num_messages: int = 5) -> str:
        """Get recent conversation as formatted string."""
        recent = self.messages[-num_messages:]
        context = []

        for msg in recent:
            context.append(f"{msg['role']}: {msg['content']}")

        return "\n".join(context)
    
    def clear(self):
        """Clear conversation history."""
        count = len(self.messages)
        self.messages = []
        logger.info(f"Cleared conversation memory ({count} messages removed)")
        
        
class PersistentMemory:
    def __init__(self, collection_name: str = "agent_memory"):
        """
        Initialize persistent memory.
        """
        self.collection_name = collection_name
        self.vector_store = load_vector_store()
        logger.info(f"Initialized persistent memory (collection: {collection_name})")
    
    def store_interaction(self, interaction: str, metadata: Dict = None):
        """
        Store an interaction in long-term memory.
        """
        if metadata is None:
            metadata = {}

        # Add timestamp if not present
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()

        # Store in vector database
        self.vector_store.add_texts(
            texts=[interaction],
            metadatas=[metadata]
        )

        logger.info(f"Stored interaction in long-term memory")
        logger.debug(f"Metadata: {metadata}")
    
    def retrieve_similar(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve similar past interactions.
        """
        results = self.vector_store.similarity_search_with_score(query, k=top_k)

        retrieved = []
        for doc, score in results:
            retrieved.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity": 1 - score
            })

        logger.info(f"Retrieved {len(retrieved)} similar interactions")
        return retrieved
    
    def get_context(self, query: str, top_k: int = 3) -> str:
        """Get relevant past interactions as formatted string."""
        results = self.retrieve_similar(query, top_k)

        if not results:
            return ""

        context_parts = []
        for i, result in enumerate(results, 1):
            timestamp = result["metadata"].get("timestamp", "Unknown")
            context_parts.append(
                f"[Past Interaction {i} - {timestamp}]\\n{result['content']}\\n"
            )

        return "\n---\n".join(context_parts)