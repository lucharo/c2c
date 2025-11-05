"""Simple C2C Manager - hardcoded everything for POC"""

import uuid
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, HookMatcher


class C2CManager:
    """Dead simple manager for conversations and sessions"""

    def __init__(self) -> None:
        # conversation_id -> {task: str, history: list[dict], session_ids: list[str]}
        self.conversations: dict[str, dict] = {}
        # session_id -> {conversation_id: str, client: ClaudeSDKClient, active: bool}
        self.sessions: dict[str, dict] = {}

    def _sanitise_task_name(self, task_name: str) -> str:
        """Sanitize task name for use in IDs"""
        # Remove spaces, convert to lowercase, keep alphanumeric and dashes
        return "".join(c if c.isalnum() or c == "-" else "-" for c in task_name.lower()).strip("-")

    def create_conversation(self, task_name: str, task_description: str) -> str:
        """Create a new conversation with a name and description"""
        sanitised_name = self._sanitise_task_name(task_name)
        conversation_id = f"conv_{sanitised_name}_{uuid.uuid4().hex[:8]}"
        self.conversations[conversation_id] = {
            "task_name": task_name,
            "task_description": task_description,
            "history": [],
            "session_ids": [],
        }
        return conversation_id

    async def start_session(self, conversation_id: str) -> str:
        """Start a new session for a conversation"""
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation {conversation_id} not found")

        session_id = f"sess_{uuid.uuid4().hex[:8]}"

        # Create agent client with hardcoded config
        options = ClaudeAgentOptions(
            cwd=Path.cwd(),
            continue_conversation=True,
            permission_mode="acceptEdits",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            hooks={},
        )
        client = ClaudeSDKClient(options)

        # Link session to conversation
        self.conversations[conversation_id]["session_ids"].append(session_id)

        # Connect client immediately
        await client.connect()

        # Store session after connecting
        self.sessions[session_id] = {
            "conversation_id": conversation_id,
            "client": client,
            "active": True,
            "connected": True,  # Now connected
        }

        # Get task description from conversation data
        task_description = self.conversations[conversation_id]["task_description"]

        # Send initial task description to start conversation (async - don't wait for response)
        await client.query(task_description)

        # Store initial task in conversation history
        self.conversations[conversation_id]["history"].append(
            {"role": "user", "content": task_description}
        )

        return session_id

    async def create_conversation_and_start_session(self, task_name: str, task_description: str) -> str:
        """Convenience: create conversation and start session"""
        conversation_id = self.create_conversation(task_name, task_description)
        return await self.start_session(conversation_id)

    async def send_message(self, session_id: str, message: str) -> str:
        """Send a message to a session (async, fire-and-forget)"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        if not session["active"]:
            raise ValueError(f"Session {session_id} is not active")

        client = session["client"]
        conversation_id = session["conversation_id"]

        # Connect client if not connected yet
        if not session.get("connected", False):
            await client.connect()
            session["connected"] = True

        # Send message to agent (async - don't wait for response)
        await client.query(message)

        # Store user message in conversation history
        self.conversations[conversation_id]["history"].append(
            {"role": "user", "content": message}
        )

        return f"Message sent to session {session_id}"

    async def receive_response(self, session_id: str) -> str:
        """Receive and collect the agent's response from a session"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        if not session["active"]:
            raise ValueError(f"Session {session_id} is not active")

        client = session["client"]
        conversation_id = session["conversation_id"]

        # Collect response from async iterator with proper termination conditions
        response_parts = []
        response_complete = False
        message_count = 0
        max_messages = 10  # Prevent infinite loops

        async for response_message in client.receive_response():
            message_count += 1

            # Extract text from content blocks
            if hasattr(response_message, 'content') and isinstance(response_message.content, list):
                for block in response_message.content:
                    if hasattr(block, 'text'):
                        text = str(block.text) if block.text else ""
                        if text.strip():
                            response_parts.append(text)
                            response_complete = True

            # Check for ResultMessage which indicates completion
            if hasattr(response_message, 'subtype') and response_message.subtype in ['success', 'error']:
                break

            # Stop if we have content or reached message limit
            if response_complete or message_count >= max_messages:
                break

        response = "".join(response_parts)

        # Store assistant response in conversation history
        self.conversations[conversation_id]["history"].append(
            {"role": "assistant", "content": response}
        )

        return response

    def end_session(self, session_id: str) -> bool:
        """End a session (keeps conversation history)"""
        if session_id not in self.sessions:
            return False

        self.sessions[session_id]["active"] = False
        return True

    def list_conversations(self) -> list[dict]:
        """List all conversations with their metadata"""
        return [
            {
                "conversation_id": conv_id,
                "task_name": conv_data["task_name"],
                "task_description": conv_data["task_description"],
                "message_count": len(conv_data["history"]),
                "session_count": len(conv_data["session_ids"]),
            }
            for conv_id, conv_data in self.conversations.items()
        ]

    def list_sessions(self) -> list[dict]:
        """List all sessions with their metadata"""
        return [
            {
                "session_id": sess_id,
                "conversation_id": sess_data["conversation_id"],
                "active": sess_data["active"],
            }
            for sess_id, sess_data in self.sessions.items()
        ]


# Global singleton instance - POC style!
manager = C2CManager()
