"""c2c: Claude Code to Claude Code Communication

MCP server for spawning and managing Claude agents.

Simple POC - just 7 tools, hardcoded config, works great!
"""

from .mcp import mcp
from .manager import manager

__all__ = ["mcp", "manager"]
