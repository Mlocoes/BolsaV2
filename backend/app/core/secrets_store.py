from datetime import datetime
from typing import Dict, Optional
from uuid import UUID

class InMemorySessionStore:
    def __init__(self):
        self._sessions: Dict[str, Dict] = {}

    async def set_session(self, token: str, user_id: UUID, expiry: datetime):
        self._sessions[token] = {
            "user_id": str(user_id),
            "expiry": expiry.isoformat(),
        }

    async def get_session(self, token: str) -> Optional[Dict]:
        session = self._sessions.get(token)
        if not session:
            return None
        expiry = datetime.fromisoformat(session["expiry"])
        if datetime.utcnow() > expiry:
            await self.delete_session(token)
            return None
        return session

    async def delete_session(self, token: str):
        self._sessions.pop(token, None)

    async def cleanup_expired(self):
        now = datetime.utcnow()
        expired = [
            t for t, s in self._sessions.items()
            if datetime.fromisoformat(s["expiry"]) <= now
        ]
        for token in expired:
            del self._sessions[token]

session_store = InMemorySessionStore()
