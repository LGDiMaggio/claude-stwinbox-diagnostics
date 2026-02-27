"""STWIN.box Sensor MCP Server - Hardware communication with STEVAL-STWINBX1."""

from .server import mcp


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


__all__ = ["main", "mcp"]
