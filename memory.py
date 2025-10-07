import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class ConversationMemory:
    def __init__(self, file_path: str = 'conversations.json'):
        self.file_path = file_path
        self.conversations = self._load_conversations()
    
    def _load_conversations(self) -> Dict:
        """Load conversations from file"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_conversations(self):
        """Save conversations to file"""
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.conversations, f, indent=2)
        except:
            pass
    
    def save_conversation(self, session_id: str, data: Dict):
        """Save conversation data"""
        self.conversations[session_id] = {
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'title': self._generate_title(data),
            'preview': self._generate_preview(data)
        }
        self._save_conversations()
    
    def get_conversation(self, session_id: str) -> Optional[Dict]:
        """Get specific conversation"""
        return self.conversations.get(session_id)
    
    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations sorted by timestamp"""
        conversations = []
        for session_id, conv in self.conversations.items():
            conversations.append({
                'session_id': session_id,
                'timestamp': conv['timestamp'],
                'title': conv['title'],
                'preview': conv['preview']
            })
        return sorted(conversations, key=lambda x: x['timestamp'], reverse=True)
    
    def delete_conversation(self, session_id: str):
        """Delete conversation"""
        if session_id in self.conversations:
            del self.conversations[session_id]
            self._save_conversations()
    
    def _generate_title(self, data: Dict) -> str:
        """Generate conversation title"""
        service_type = data.get('type', 'General')
        return f"{service_type.title()} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    def _generate_preview(self, data: Dict) -> str:
        """Generate conversation preview"""
        answers = data.get('answers', [])
        if answers:
            return answers[0][:100] + "..." if len(answers[0]) > 100 else answers[0]
        return "No content"