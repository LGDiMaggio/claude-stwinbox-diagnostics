# Getting Started Guide

## Prerequisites

- **Hardware**: STEVAL-STWINBX1 (STWIN.box) with USB-C cable
- **Firmware**: FP-AI-MONITOR2 or FP-SNS-DATALOG2 flashed on the board
- **Software**:
  - Python 3.10+
  - [uv](https://docs.astral.sh/uv/) package manager
  - Claude Desktop (or API access)

## Step 1: Flash the Firmware

1. Download [FP-AI-MONITOR2](https://www.st.com/en/embedded-software/fp-ai-monitor2.html) from ST
2. Flash using STM32CubeProgrammer via the ST-LINK connector
3. Alternatively, use FP-SNS-DATALOG2 for high-speed data logging

## Step 2: Install MCP Servers

```bash
# Clone the repository
git clone https://github.com/LGDiMaggio/claude-stwinbox-diagnostics.git
cd claude-stwinbox-diagnostics

# Install both servers (uv handles virtual environments automatically)
cd mcp-servers/stwinbox-sensor-mcp
uv sync

cd ../vibration-analysis-mcp
uv sync
```

## Step 3: Configure Claude Desktop

Edit your Claude Desktop configuration file:

- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the MCP servers:

```json
{
  "mcpServers": {
    "stwinbox-sensor": {
      "command": "uv",
      "args": [
        "--directory", "C:/path/to/mcp-servers/stwinbox-sensor-mcp",
        "run", "stwinbox-sensor-mcp"
      ]
    },
    "vibration-analysis": {
      "command": "uv",
      "args": [
        "--directory", "C:/path/to/mcp-servers/vibration-analysis-mcp",
        "run", "vibration-analysis-mcp"
      ]
    }
  }
}
```

Replace `C:/path/to/` with the actual path to your clone.

## Step 4: Install Skills

### Option A: Claude.ai (Web)
1. Zip each skill folder individually:
   - `skills/machine-vibration-monitoring/` → `machine-vibration-monitoring.zip`
   - `skills/vibration-fault-diagnosis/` → `vibration-fault-diagnosis.zip`
   - `skills/operator-diagnostic-report/` → `operator-diagnostic-report.zip`
2. Upload each zip in Claude.ai project settings under "Skills"

### Option B: Claude Desktop
1. Place the skill folders in your Claude Desktop skills directory
2. Or reference them in the project configuration

## Step 5: Connect the STWIN.box

1. Connect the STWIN.box to your PC via USB-C
2. Check that a COM port appears (Windows) or `/dev/ttyACM*` (Linux/Mac)
3. Start Claude Desktop and try:

> "Connect to the STWIN.box and show me the available sensors"

Claude will use the **machine-vibration-monitoring** skill to:
- Find the COM port
- Connect to the board
- List available sensors with their current configuration

## Step 6: First Measurement

Ask Claude:

> "I have a centrifugal pump running at 1470 RPM with 6205 bearings. 
> Can you take a vibration measurement and tell me if everything looks healthy?"

Claude will:
1. Configure the IIS3DWB sensor for wideband vibration
2. Acquire 2+ seconds of data
3. Compute the FFT spectrum
4. Calculate bearing fault frequencies for 6205 at 1470 RPM
5. Run envelope analysis for bearing condition
6. Classify any detected faults
7. Report ISO 10816 severity
8. Present findings in plain language

## Troubleshooting

### Board not detected
- Check USB cable (must support data, not charge-only)
- Try a different USB port
- On Windows, check Device Manager for the COM port
- Install ST USB drivers if needed

### Serial connection timeout
- Ensure the correct firmware is flashed
- Try baud rate 115200 (default for FP-AI-MONITOR2)
- Reset the board (press the reset button)

### No vibration data
- Check sensor configuration (use `list_sensors` and `get_sensor_config`)
- Ensure the sensor is enabled and ODR is set
- For IIS3DWB: ODR is fixed at 26667 Hz

### MCP server not appearing in Claude
- Check `claude_desktop_config.json` syntax (valid JSON)
- Verify the path to the MCP server directory
- Ensure `uv` is installed and in PATH
- Restart Claude Desktop after config changes
