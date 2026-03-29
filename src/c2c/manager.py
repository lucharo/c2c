"""Simple C2C Manager - Unified conversation model (matching c2c_dev pattern)"""

import asyncio
import uuid
from pathlib import Path
from datetime import datetime
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


class C2CManager:
    """Simple manager with unified conversation model (no separate sessions)"""

    def __init__(self) -> None:
        # Active conversations: conversation_id -> {client, history, metadata}
        self.active: dict[str, dict] = {}

    def _sanitise_task_name(self, task_name: str) -> str:
        """Sanitize task name for use in IDs"""
        return "".join(c if c.isalnum() or c == "-" else "-" for c in task_name.lower()).strip("-")

    async def create_conversation(self, task_name: str, task_description: str) -> str:
        """Create a new conversation and start Agent SDK client

        Args:
            task_name: Short name for the task (used in ID)
            task_description: Full description/prompt for the agent

        Returns:
            conversation_id string
        """
        async def _internal():
            # Generate conversation ID
            sanitised_name = self._sanitise_task_name(task_name)
            conversation_id = f"conv_{sanitised_name}_{uuid.uuid4().hex[:8]}"

            # Create Agent SDK client
            options = ClaudeAgentOptions(
                cwd=Path.cwd(),
                continue_conversation=True,
                permission_mode="acceptEdits",
                allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
                hooks={},
            )
            client = ClaudeSDKClient(options)

            # Connect client
            await client.connect()

            # Store conversation
            self.active[conversation_id] = {
                "client": client,
                "task_name": task_name,
                "task_description": task_description,
                "history": [],
                "created_at": datetime.now(),
                "status": "active",
            }

            # Send initial task (async - don't wait for response)
            await client.query(task_description)

            # Store initial user message in history
            self.active[conversation_id]["history"].append({
                "role": "user",
                "content": task_description,
                "timestamp": datetime.now().isoformat()
            })

            return conversation_id

        return await asyncio.wait_for(_internal(), timeout=30)

    async def resume_conversation(self, conversation_id: str) -> str:
        """Resume an existing conversation (placeholder for future storage integration)

        Args:
            conversation_id: The conversation to resume

        Returns:
            conversation_id string
        """
        # TODO: Load from storage, create new client, restore history
        raise NotImplementedError("Resume conversation not yet implemented - needs storage integration")

    async def send_message_and_receive_response(self, conversation_id: str, message: str) -> str:
        """Send a message and immediately receive response (following official Agent SDK pattern)

        Args:
            conversation_id: The conversation to send message to
            message: The message content

        Returns:
            The agent's response string
        """
        if conversation_id not in self.active:
            raise ValueError(f"Conversation {conversation_id} not found or not active")

        conversation = self.active[conversation_id]
        client = conversation["client"]

        # Store user message in conversation history
        conversation["history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })

        # Send message and collect response immediately (official Agent SDK pattern)
        response_parts = []
        response_complete = False
        message_count = 0
        max_messages = 10  # Prevent infinite loops

        await client.query(message)

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

        # Store agent response in conversation history
        conversation["history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        return response

    async def end_conversation(self, conversation_id: str) -> None:
        """End a conversation (cleanup, no storage yet)

        Args:
            conversation_id: The conversation to end
        """
        if conversation_id not in self.active:
            raise ValueError(f"Conversation {conversation_id} not found or not active")

        conversation = self.active[conversation_id]

        # TODO: Save to persistent storage here

        # Clean up
        del self.active[conversation_id]

    def list_conversations(self) -> list[dict]:
        """List all active conversations

        Returns:
            List of conversation metadata dicts
        """
        return [
            {
                "conversation_id": conv_id,
                "task_name": conv_data["task_name"],
                "task_description": conv_data["task_description"],
                "message_count": len(conv_data["history"]),
                "status": conv_data["status"],
                "created_at": conv_data["created_at"].isoformat(),
            }
            for conv_id, conv_data in self.active.items()
        ]


# Global singleton instance
manager = C2CManager()
