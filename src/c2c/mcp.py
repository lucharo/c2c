"""C2C MCP Server - Simplified conversation model using raw MCP Server pattern

Uses direct MCP Server (like c2c_dev) with unified conversation model (no sessions).
"""

import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool
from .manager import manager

# Create raw MCP server (like c2c_dev)
app = Server("c2c")


@app.list_tools()
async def list_tools():
    """List all available C2C tools"""
    return [
        Tool(
            name="create_conversation",
            description="Create a new conversation with Agent SDK",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_name": {"type": "string", "description": "Short name for the task (used in ID)"},
                    "task_description": {"type": "string", "description": "Full description/prompt for the agent"},
                },
                "required": ["task_name", "task_description"]
            }
        ),
        Tool(
            name="send_message_and_receive_response",
            description="Send a message to a conversation and receive the response immediately",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "description": "The conversation to send message to"},
                    "message": {"type": "string", "description": "The message content"},
                },
                "required": ["conversation_id", "message"]
            }
        ),
        Tool(
            name="end_conversation",
            description="End a conversation and cleanup",
            inputSchema={
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string", "description": "The conversation to end"},
                },
                "required": ["conversation_id"]
            }
        ),
        Tool(
            name="list_conversations",
            description="List all active conversations",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls - directly call manager methods"""
    import sys
    print(f"[C2C MCP] Received tool call: {name}", file=sys.stderr, flush=True)
    print(f"[C2C MCP] Arguments: {arguments}", file=sys.stderr, flush=True)

    try:
        if name == "create_conversation":
            print(f"[C2C MCP] Calling manager.create_conversation...", file=sys.stderr, flush=True)
            conversation_id = await manager.create_conversation(
                arguments["task_name"],
                arguments["task_description"]
            )
            print(f"[C2C MCP] Got conversation_id: {conversation_id}", file=sys.stderr, flush=True)

            result = {
                "content": [{
                    "type": "text",
                    "text": f"""Conversation {conversation_id} created successfully!

Task description: {arguments['task_description']}

Use send_message_and_receive_response with conversation_id '{conversation_id}' and the task description as the message to start the agent."""
                }]
            }
            print(f"[C2C MCP] Returning result to Claude Code", file=sys.stderr, flush=True)
            return result

        elif name == "send_message_and_receive_response":
            response = await manager.send_message_and_receive_response(
                arguments["conversation_id"],
                arguments["message"]
            )
            return {
                "content": [{
                    "type": "text",
                    "text": response
                }]
            }

        elif name == "end_conversation":
            await manager.end_conversation(arguments["conversation_id"])
            return {
                "content": [{
                    "type": "text",
                    "text": f"Ended conversation {arguments['conversation_id']}"
                }]
            }

        elif name == "list_conversations":
            conversations = manager.list_conversations()
            if not conversations:
                text = "No active conversations"
            else:
                lines = ["Active Conversations:"]
                for conv in conversations:
                    lines.append(
                        f"  {conv['conversation_id']}: {conv['task_name']} - {conv['task_description']} "
                        f"({conv['message_count']} messages, status: {conv['status']})"
                    )
                text = "\n".join(lines)
            return {
                "content": [{
                    "type": "text",
                    "text": text
                }]
            }

        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }]
            }

    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }]
        }


async def run_async():
    """Run the MCP server (like c2c_dev)"""
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


def main():
    """Entry point"""
    asyncio.run(run_async())


if __name__ == "__main__":
    main()
