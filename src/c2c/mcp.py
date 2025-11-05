"""C2C MCP Server - 8 tools in one place"""

from mcp.server.fastmcp import FastMCP
from .manager import manager

# Create the MCP server
mcp = FastMCP("c2c")


@mcp.tool()
async def create_conversation(task_name: str, task_description: str) -> str:
    """Create a new conversation with a name and description

    Args:
        task_name: Short name for the task (used in IDs)
        task_description: Full description/prompt for the agent

    Returns:
        conversation_id string
    """
    conversation_id = manager.create_conversation(task_name, task_description)
    return f"Created conversation {conversation_id} - {task_name}: {task_description}"


@mcp.tool()
async def start_session(conversation_id: str) -> str:
    """Start a new session for an existing conversation

    Args:
        conversation_id: The conversation to start a session for

    Returns:
        session_id string
    """
    try:
        session_id = await manager.start_session(conversation_id)
        return f"Started session {session_id} for conversation {conversation_id}"
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
async def create_conversation_and_start_session(task_name: str, task_description: str) -> str:
    """Create a conversation and start a session in one go

    Args:
        task_name: Short name for the task (used in IDs)
        task_description: Full description/prompt for the agent

    Returns:
        session_id string
    """
    session_id = await manager.create_conversation_and_start_session(task_name, task_description)
    return f"Created conversation and started session {session_id} - {task_name}: {task_description}"


@mcp.tool()
async def send_message(session_id: str, message: str) -> str:
    """Send a message to an active session (async, returns immediately)

    Args:
        session_id: The session to send the message to
        message: The message content

    Returns:
        Confirmation that message was sent
    """
    try:
        result = await manager.send_message(session_id, message)
        return result
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
async def receive_response(session_id: str) -> str:
    """Receive the agent's response from a session

    Args:
        session_id: The session to receive response from

    Returns:
        The agent's response
    """
    try:
        response = await manager.receive_response(session_id)
        return response
    except ValueError as e:
        return f"Error: {e}"


@mcp.tool()
async def end_session(session_id: str) -> str:
    """End an active session (conversation history is preserved)

    Args:
        session_id: The session to end

    Returns:
        Success message
    """
    success = manager.end_session(session_id)
    if success:
        return f"Ended session {session_id}"
    else:
        return f"Session {session_id} not found"


@mcp.tool()
async def list_conversations() -> str:
    """List all conversations

    Returns:
        Formatted list of conversations
    """
    conversations = manager.list_conversations()
    if not conversations:
        return "No conversations yet"

    lines = ["Conversations:"]
    for conv in conversations:
        lines.append(
            f"  {conv['conversation_id']}: {conv['task_name']} - {conv['task_description']} "
            f"({conv['message_count']} messages, {conv['session_count']} sessions)"
        )
    return "\n".join(lines)


@mcp.tool()
async def list_sessions() -> str:
    """List all sessions

    Returns:
        Formatted list of sessions
    """
    sessions = manager.list_sessions()
    if not sessions:
        return "No sessions yet"

    lines = ["Sessions:"]
    for sess in sessions:
        status = "active" if sess["active"] else "ended"
        lines.append(
            f"  {sess['session_id']}: conversation {sess['conversation_id']} ({status})"
        )
    return "\n".join(lines)


def main() -> None:
    """Run the C2C MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
