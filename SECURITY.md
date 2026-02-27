# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ Current |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT** open a public issue
2. Email the maintainer or use GitHub's private vulnerability reporting feature
3. Include a description of the vulnerability and steps to reproduce

## Security Considerations

This project involves:
- **Serial port access**: The stwinbox-sensor-mcp server accesses USB serial ports. Ensure only trusted users can run the MCP server.
- **Local execution**: MCP servers run locally. Sensor data stays on the local machine (except when sent to the Claude API for analysis).
- **No network listeners**: Both MCP servers use STDIO transport — they do not open network ports.
- **Data sensitivity**: Vibration signatures can reveal proprietary machine information. Handle exported data appropriately.
