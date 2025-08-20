import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class ConversationMemory:
    def __init__(self, storage_file='conversations.json'):
        self.storage_file = storage_file
        self.conversations = self.load_conversations()
    
    def load_conversations(self) -> Dict:
        """Load conversations from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_conversations(self):
        """Save conversations to file"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.conversations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving conversations: {e}")
    
    def save_conversation(self, session_id: str, conversation_data: Dict):
        """Save a conversation"""
        self.conversations[session_id] = {
            'timestamp': datetime.now().isoformat(),
            'title': self.generate_title(conversation_data),
            'data': conversation_data
        }
        self.save_conversations()
    
    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get a specific conversation"""
        return self.conversations.get(session_id)
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations sorted by timestamp"""
        conversations = []
        for session_id, conv in self.conversations.items():
            conversations.append({
                'session_id': session_id,
                'timestamp': conv['timestamp'],
                'title': conv['title'],
                'preview': self.generate_preview(conv['data'])
            })
        return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)
    
    def delete_conversation(self, session_id: str):
        """Delete a conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            self.save_conversations()
    
    def generate_title(self, conversation_data: Dict) -> str:
        """Generate a title for the conversation"""
        issue_type = conversation_data.get('type', 'General')
        user_selections = conversation_data.get('user_selections', {})
        db_system = user_selections.get('database', 'Database')
        
        return f"{issue_type.title()} - {db_system}"
    
    def generate_preview(self, conversation_data: Dict) -> str:
        """Generate a preview of the conversation"""
        answers = conversation_data.get('answers', [])
        if answers:
            preview = answers[0][:100]
            return preview + "..." if len(answers[0]) > 100 else preview
        return "No messages yet"