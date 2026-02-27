"""Vibration Analysis MCP Server - Signal processing and fault detection."""

from .server import mcp


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


__all__ = ["main", "mcp"]
