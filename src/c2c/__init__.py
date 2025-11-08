"""c2c: Claude Code to Claude Code Communication

MCP server for spawning and managing Claude agents.
"""

# Export the MCP server for compatibility
from .mcp import app as mcp

__all__ = ["mcp"]