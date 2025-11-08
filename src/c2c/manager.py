"""Simple C2C Manager - Unified conversation model (matching c2c_dev pattern)"""

import asyncio
import uuid
from pathlib import Path
from datetime import datetime
import threading
import queue
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions


class ConversationWorkerThread(threading.Thread):
    """Dedicated thread for running Agent SDK operations"""

    def __init__(self, client_options):
        super().__init__(daemon=True)
        self.client_options = client_options
        self.client = None
        self.loop = None
        self.task_queue = queue.Queue()
        self.running = True
        self.start()

    def run(self):
        """Run the event loop in this dedicated thread"""
        import sys
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def process_tasks():
            # Create and connect client once
            print(f"[Worker Thread] Creating client", file=sys.stderr, flush=True)
            self.client = ClaudeSDKClient(self.client_options)
            await self.client.connect()
            print(f"[Worker Thread] Client connected", file=sys.stderr, flush=True)

            # Process tasks from queue
            while self.running:
                try:
                    task = self.task_queue.get(timeout=0.1)
                    if task is None:
                        break

                    coro, result_queue = task
                    try:
                        result = await coro(self.client)
                        result_queue.put(("success", result))
                    except Exception as e:
                        result_queue.put(("error", e))
                except queue.Empty:
                    continue

        self.loop.run_until_complete(process_tasks())
        self.loop.close()

    def submit_task(self, coro):
        """Submit a coroutine to run in this thread's event loop"""
        result_queue = queue.Queue()
        self.task_queue.put((coro, result_queue))
        status, result = result_queue.get()
        if status == "error":
            raise result
        return result

    def stop(self):
        """Stop the worker thread"""
        self.running = False
        self.task_queue.put(None)


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
        import sys
        print(f"[C2C Manager] Creating conversation: {task_name}", file=sys.stderr, flush=True)

        # Generate conversation ID
        sanitised_name = self._sanitise_task_name(task_name)
        conversation_id = f"conv_{sanitised_name}_{uuid.uuid4().hex[:8]}"
        print(f"[C2C Manager] Generated ID: {conversation_id}", file=sys.stderr, flush=True)

        # Create client options
        client_options = ClaudeAgentOptions(
            cwd=Path.cwd(),
            continue_conversation=True,
            permission_mode="acceptEdits",
            allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
            hooks={},
        )

        # Create dedicated worker thread for this conversation
        worker = ConversationWorkerThread(client_options)

        # Store conversation
        self.active[conversation_id] = {
            "worker": worker,
            "task_name": task_name,
            "task_description": task_description,
            "history": [],
            "created_at": datetime.now(),
            "status": "active",
        }
        print(f"[C2C Manager] Stored conversation with worker thread", file=sys.stderr, flush=True)

        print(f"[C2C Manager] Conversation ready, returning conversation_id: {conversation_id}", file=sys.stderr, flush=True)
        return conversation_id

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
            message: The message content (can be empty to just collect pending responses)

        Returns:
            The agent's response string
        """
        import sys
        if conversation_id not in self.active:
            raise ValueError(f"Conversation {conversation_id} not found or not active")

        conversation = self.active[conversation_id]
        worker = conversation["worker"]

        # Define the task to run in the worker thread
        async def query_task(client):
            # Check if we need to send a new query or just collect pending response
            if message and message.strip():
                # Store user message in conversation history only if sending new message
                print(f"[C2C Manager] Sending new query: {message[:50]}...", file=sys.stderr, flush=True)
                await client.query(message)
            else:
                print(f"[C2C Manager] Collecting pending response (no new query)", file=sys.stderr, flush=True)

            # Collect response
            response_parts = []
            response_complete = False
            message_count = 0
            max_messages = 10

            async for response_message in client.receive_response():
                message_count += 1

                if hasattr(response_message, 'content') and isinstance(response_message.content, list):
                    for block in response_message.content:
                        if hasattr(block, 'text'):
                            text = str(block.text) if block.text else ""
                            if text.strip():
                                response_parts.append(text)
                                response_complete = True

                if hasattr(response_message, 'subtype') and response_message.subtype in ['success', 'error']:
                    break

                if response_complete or message_count >= max_messages:
                    break

            return "".join(response_parts)

        # Submit task to worker thread and wait for result
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, worker.submit_task, query_task)

        # Store in history
        if message and message.strip():
            conversation["history"].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })

        conversation["history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })

        print(f"[C2C Manager] Response received: {response[:100]}...", file=sys.stderr, flush=True)
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
