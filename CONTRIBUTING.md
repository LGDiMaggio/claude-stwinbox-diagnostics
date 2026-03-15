# Contributing to Claude STWIN.box Diagnostics

Thanks for contributing. This repository is an open-source PoC for industrial vibration diagnostics with Claude + MCP + STEVAL-STWINBX1. We prioritize technical rigor, reproducibility, and transparent limitations over hype.

## Before you start

- Read [README.md](README.md) for scope and current limitations.
- Read [SECURITY.md](SECURITY.md) for responsible disclosure.
- Check open [issues](https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/issues) and [discussions](https://github.com/LGDiMaggio/claude-stwinbox-diagnostics/discussions) to avoid duplicate work.

## Local setup

## 1) Clone

```bash
git clone https://github.com/LGDiMaggio/claude-stwinbox-diagnostics.git
cd claude-stwinbox-diagnostics
```

## 2) Install editable MCP servers

```bash
uv pip install -e mcp-servers/stwinbox-sensor-mcp -e mcp-servers/vibration-analysis-mcp
```

## 3) Optional: enable FP-SNS-DATALOG2 SDK features

The ST `stdatalog-pysdk` packages are not published on PyPI. If your contribution requires DATALOG2 live USB acquisition or native `.dat` folder loading, follow setup notes in [README.md](README.md) and `mcp-servers/*/README.md`.

## Contribution flow (code + docs)

1. **Fork** and create a branch from `main`.
   - Naming convention suggestion: `fix/<short-topic>`, `feat/<short-topic>`, `docs/<short-topic>`
2. **Implement change** with clear, minimal scope.
3. **Update docs** for any behavior/tooling change (README, server README, examples, skills references).
4. **Run checks** that are relevant to your change.
5. **Commit with clear message** (imperative mood, one concern per commit when practical).
6. **Open a pull request** using the PR template.

## What to include in a pull request

- Problem statement and motivation.
- What changed and why.
- Any limitations/trade-offs.
- Reproducible validation steps (commands + sample input assumptions).
- If diagnostics behavior changed: before/after evidence.

## Reporting bugs

Use the **Bug Report** issue template and include:

- OS + Python version.
- Which MCP server(s) were involved.
- STWIN.box firmware and acquisition mode.
- Minimal reproducible steps.
- Sample data characteristics (sampling rate, duration, signal axis, expected fault signature).

## Proposing enhancements

Use the **Feature Request** template and include:

- Concrete use case (machine type / operating regime).
- Why current behavior is insufficient.
- Proposed API or workflow impact.
- Validation strategy.

## Contribution etiquette

- Be respectful and specific in technical discussions.
- Prefer evidence-backed claims (plots, spectra, references, standards).
- Document uncertainty explicitly when data is incomplete.
- Avoid introducing scope creep unrelated to the stated PoC direction.
- Keep changes reviewable; split very large work into multiple PRs.

## Review process (lightweight)

1. Maintainer triages PR (scope, clarity, reproducibility).
2. Technical review checks correctness and documentation alignment.
3. Feedback round(s) for fixes/clarifications.
4. Merge when change is coherent, tested at appropriate level, and documented.

Typical outcomes:
- **Approve and merge**
- **Request changes** (most common for first PRs)
- **Close with explanation** if out of scope

## Good first issues (suggested)

- Add unit tests for edge cases in FFT/envelope helper functions.
- Improve error messages in MCP tool responses for invalid inputs.
- Add minimal sample datasets and expected output snapshots in `examples/`.
- Clarify docs for Windows vs Linux MCP launch paths.
- Add references/citations to vibration standards in skill docs where missing.
- Improve issue template wording based on real user reports.

## Public roadmap

See [docs/roadmap.md](docs/roadmap.md). If you want to work on a roadmap item, comment on an issue first so effort can be coordinated.

## License

By contributing, you agree your contributions will be licensed under the Apache License 2.0.
