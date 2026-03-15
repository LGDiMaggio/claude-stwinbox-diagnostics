# Demo assets guide

This document describes recommended demo assets for technical communication (README, talks, docs, release notes) without overstating project maturity.

## Principles

- Show real workflows and real outputs where possible.
- Avoid implying production readiness.
- Include context (sensor, sampling rate, operating condition, assumptions).
- Prefer short clips/GIFs with readable captions.

## Recommended assets to produce

## 1) End-to-end workflow GIF (30-60s)

**Goal:** Show complete flow from acquisition to conversational diagnosis.

- Start acquisition from STWIN.box (or load sample file).
- Run one MCP analysis tool (`compute_fft_spectrum`, `diagnose_vibration`, etc.).
- Show Claude interaction and generated interpretation.

**Recommended caption fields:**
- board/firmware
- signal duration + sampling rate
- analysis tools invoked
- note that this is PoC output

## 2) Diagnostic evidence screenshots

Capture static images for each representative diagnostic scenario:

- Normal baseline spectrum
- Unbalance signature
- Misalignment signature
- Bearing fault envelope peak example

For each screenshot include:
- axis and units
- RPM and harmonics markers (if used)
- dataset provenance (synthetic vs recorded)

## 3) Report-generation sample

Include one operator-facing report artifact with:
- machine context
- findings + confidence caveats
- recommended next inspections

## 4) Setup walkthrough clip

A short setup video for first-time contributors:
- install servers
- configure MCP client
- run first command

## Asset checklist before publishing

- [ ] No confidential machine/customer data visible.
- [ ] Any synthetic data is labeled as synthetic.
- [ ] PoC disclaimer included where appropriate.
- [ ] Command/output text is readable at 1080p.
- [ ] Version/date of workflow is noted.

## Suggested file organization

- `docs/images/` for static screenshots and diagrams.
- `docs/videos/` for short MP4 demos (if added).
- `releases/` attachments for versioned demo bundles.
