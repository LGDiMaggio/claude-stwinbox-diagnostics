# Example Usage

## Generating Sample Data

To create synthetic vibration signals for testing (no hardware required):

```bash
cd examples
python generate_sample_data.py
```

This creates three JSON files in `examples/sample_data/`:

| File | Description | Expected Diagnosis |
|------|------------|-------------------|
| `healthy_pump.json` | Normal pump vibration | Healthy |
| `unbalance_motor.json` | Motor with rotor unbalance | Unbalance (1× dominant) |
| `bearing_fault_outer.json` | Pump with outer-race bearing defect | BPFO in envelope spectrum |

## Testing with Claude

### Without hardware (analysis only)

Configure only the **vibration-analysis-mcp** server and install the skills.
Then ask Claude:

> "I have a vibration data file at examples/sample_data/unbalance_motor.json. 
> Can you analyze it and tell me what's wrong with the machine?"

### With STWIN.box connected

Configure both MCP servers and ask:

> "Connect to the STWIN.box on COM3 and take a vibration measurement 
> of my pump running at 1470 RPM"

## Sample Data Format

Each JSON file contains:

```json
{
  "signal": [0.012, -0.008, ...],     // Time-domain samples (acceleration in g)
  "sample_rate_hz": 26667.0,           // Sampling frequency
  "duration_s": 2.0,                   // Recording duration
  "n_samples": 53334,                  // Number of samples
  "metadata": {
    "description": "...",
    "machine": "...",
    "rpm": 1470.0,
    "sensor": "IIS3DWB",
    "axis": "radial_horizontal",
    "units": "g",
    "expected_diagnosis": "..."
  }
}
```
