# Contributing to Claude STWIN.box Diagnostics

Thank you for your interest in contributing! This project connects industrial edge sensors to LLM-based diagnostics, and contributions from the vibration analysis, embedded systems, and AI communities are all welcome.

## How to Contribute

### Reporting Issues
- Use [GitHub Issues](https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/issues)
- Include your Python version, OS, and STWIN.box firmware version if relevant
- For analysis bugs, include sample data (or describe the signal characteristics)

### Suggesting Features
- Open an issue with the `enhancement` label
- Describe the use case and expected behavior

### Code Contributions

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch** from `main`: `git checkout -b feature/my-feature`
4. **Make changes** — follow the code style below
5. **Test** your changes (see [Testing](#testing))
6. **Commit** with clear messages: `git commit -am 'Add envelope analysis for tapered roller bearings'`
7. **Push** to your fork: `git push origin feature/my-feature`
8. **Open a Pull Request** against `main`

### What We're Looking For

| Area | Examples |
|------|---------|
| **New bearing data** | Add bearings to `COMMON_BEARINGS` in `bearing_freqs.py` |
| **Fault signatures** | New fault detection rules in `fault_detection.py` |
| **Signal processing** | Additional analysis methods (cepstrum, wavelet, etc.) |
| **Sensor support** | Support for additional ST sensor boards |
| **Skills** | New Claude skills for different diagnostic workflows |
| **Documentation** | Tutorials, translations, improved guides |
| **Tests** | Unit tests for analysis functions |

## Code Style

- Python 3.10+ with type hints
- Use `from __future__ import annotations` for forward references
- Docstrings in Google style
- Maximum line length: 100 characters (soft limit)
- Use `numpy` and `scipy` for numerical code

## Testing

```bash
# Install development dependencies
cd mcp-servers/vibration-analysis-mcp
uv sync

# Run tests (when available)
uv run pytest tests/
```

## MCP Server Development

When adding new MCP tools:
1. Add the function in the appropriate module (e.g., `fft_analysis.py`)
2. Expose it as an `@mcp.tool()` in `server.py`
3. Write a clear docstring — Claude uses the docstring to understand when to call the tool
4. Update the server's README with the new tool

## Skill Development

When creating or modifying Claude skills:
1. Follow the [Anthropic Skills Guide](https://docs.anthropic.com) format
2. SKILL.md must have proper YAML frontmatter (`name`, `description`, `dependencies`, `tags`)
3. Use `kebab-case` for skill folder names
4. Keep reference docs focused — Claude reads them on every invocation
5. Test with Claude Desktop or Claude.ai

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
