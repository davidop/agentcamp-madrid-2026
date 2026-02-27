#!/usr/bin/env python3
"""
Intelligent pipeline that orchestrates the full documentation generation flow:
  1. Scrape  – extract information from the project and (optionally) remote URLs
  2. Analyze – derive architecture, services, events from the scraped data
  3. Generate – produce Mermaid diagrams and structured Markdown documentation

This pipeline demonstrates combining .NET Aspire, MCP Agents, Python scraping, and
Mermaid visualisation as shown at AgentCamp Madrid 2026.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
# Allow running from any working directory
_ROOT = Path(__file__).parent
sys.path.insert(0, str(_ROOT))

from scraper import scrape_project_files, scrape_url, extract_aspire_metadata, save_scrape_results


# ---------------------------------------------------------------------------
# Mermaid diagram generators
# ---------------------------------------------------------------------------

def build_architecture_diagram(metadata: dict) -> str:
    """Generate a Mermaid graph TB diagram from Aspire metadata."""
    lines = ["graph TB"]
    lines.append("    %% Orchestrator")
    lines.append("    AppHost[AspireApp2.AppHost<br/>🎯 Orchestrator]")
    lines.append("")

    # Services
    if metadata["services"]:
        lines.append("    %% Application services")
        for svc in metadata["services"]:
            label = f"{svc['class']}<br/>🔗 {svc['name']}"
            lines.append(f"    {svc['name']}[{label}]")
        lines.append("")

    # Resources
    if metadata["resources"]:
        lines.append("    %% External resources")
        for res in metadata["resources"]:
            lines.append(f"    {res['name']}[({res['name']}<br/>💾 {res['type']})]")
        lines.append("")

    # Orchestration edges (AppHost → each service/resource)
    lines.append("    %% Orchestration")
    for svc in metadata["services"]:
        lines.append(f"    AppHost -.->|orchestrates| {svc['name']}")
    for res in metadata["resources"]:
        lines.append(f"    AppHost -.->|manages| {res['name']}")
    lines.append("")

    # Dependency edges
    if metadata["dependencies"]:
        lines.append("    %% Dependencies")
        seen_edges = set()
        for dep in metadata["dependencies"]:
            if isinstance(dep, dict):
                from_svc = dep.get("from", "")
                to_res = dep.get("to", "")
            else:
                # Legacy string format — skip
                continue
            edge = (from_svc, to_res)
            if edge not in seen_edges:
                seen_edges.add(edge)
                lines.append(f"    {from_svc} -->|uses| {to_res}")

    lines.append("")
    lines.append("    %% Styling")
    lines.append("    classDef orchestrator fill:#e1f5fe,stroke:#01579b,stroke-width:2px")
    lines.append("    classDef service fill:#f3e5f5,stroke:#4a148c,stroke-width:2px")
    lines.append("    classDef resource fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px")
    lines.append("    class AppHost orchestrator")
    if metadata["services"]:
        names = ",".join(s["name"] for s in metadata["services"])
        lines.append(f"    class {names} service")
    if metadata["resources"]:
        names = ",".join(r["name"] for r in metadata["resources"])
        lines.append(f"    class {names} resource")

    return "```mermaid\n" + "\n".join(lines) + "\n```"


def build_event_flow_diagram(metadata: dict) -> str:
    """Generate a Mermaid sequenceDiagram showing the startup event flow."""
    lines = ["sequenceDiagram"]
    lines.append("    autonumber")
    lines.append("    participant AppHost as 🎯 AppHost")

    for res in metadata["resources"]:
        lines.append(f"    participant {res['name']} as 💾 {res['name']}")
    for svc in metadata["services"]:
        lines.append(f"    participant {svc['name']} as 🔗 {svc['name']}")

    lines.append("")
    lines.append("    Note over AppHost: Application startup")
    lines.append("")

    # Resources start first
    for res in metadata["resources"]:
        lines.append(f"    AppHost->>+{res['name']}: start container")
        lines.append(f"    {res['name']}-->>-AppHost: ready ✅")

    lines.append("")

    # Services start after their resources
    for svc in metadata["services"]:
        lines.append(f"    AppHost->>+{svc['name']}: start service")
        for dep in metadata["dependencies"]:
            if isinstance(dep, dict) and dep.get("from") == svc["name"]:
                to_name = dep["to"]
                lines.append(f"    {svc['name']}->>+{to_name}: health check")
                lines.append(f"    {to_name}-->>-{svc['name']}: healthy ✅")
        lines.append(f"    {svc['name']}-->>-AppHost: ready ✅")

    lines.append("")
    lines.append("    Note over AppHost: All services healthy — pipeline complete")

    return "```mermaid\n" + "\n".join(lines) + "\n```"


def build_pipeline_diagram() -> str:
    """Generate a Mermaid flowchart showing the documentation pipeline itself."""
    return """```mermaid
flowchart LR
    A([🐍 scraper.py]) -->|project files + URLs| B([🔍 extract_aspire_metadata])
    B -->|structured metadata| C([📊 build_architecture_diagram])
    B -->|structured metadata| D([📋 build_event_flow_diagram])
    C -->|Mermaid graph TB| E([📝 generate_documentation])
    D -->|Mermaid sequenceDiagram| E
    E -->|SolutionOverview-*.md| F([📁 docs/])
    F -->|review| G([🤖 MCP Agent])
    G -->|enrich + validate| F

    style A fill:#fff9c4,stroke:#f9a825
    style G fill:#e8f5e9,stroke:#2e7d32
```"""


# ---------------------------------------------------------------------------
# Documentation generator
# ---------------------------------------------------------------------------

def generate_documentation(metadata: dict, scrape_summary: dict, timestamp: str) -> str:
    """Compose the full Markdown documentation file."""

    arch_diagram = build_architecture_diagram(metadata)
    event_diagram = build_event_flow_diagram(metadata)
    pipeline_diagram = build_pipeline_diagram()

    service_rows = "\n".join(
        f"| `{s['name']}` | `{s['class']}` | .NET Aspire project |"
        for s in metadata["services"]
    )
    resource_rows = "\n".join(
        f"| `{r['name']}` | `{r['type'].replace('Add', '')}` | External container |"
        for r in metadata["resources"]
    )
    endpoint_rows = "\n".join(
        f"| `{e['method']}` | `{e['path']}` | `{e['file']}` |"
        for e in metadata["endpoints"]
    )

    return f"""# Solution Overview

## Overview

This solution is a **.NET Aspire**-based distributed application generated and documented automatically
by the AgentCamp Madrid 2026 pipeline — combining **Aspire**, **MCP Agents**, **Python scraping**, and
**Mermaid visualisation**.

## Goal and Purpose

- Demonstrate automated documentation generation from a live microservices solution
- Show how Python scraping + AI agents can extract and enrich architecture knowledge
- Produce Mermaid diagrams (architecture, event flows, pipeline) as first-class documentation artefacts
- Provide a continuous pipeline from code → documentation ready for production

## Documentation Pipeline

{pipeline_diagram}

## Architecture

### Architecture Diagram (Mermaid)

{arch_diagram}

### Architecture Diagram (ASCII)

```
+---------------------------+
|  AspireApp2.AppHost       |
|  🎯 Orchestrator          |
+---------------------------+
    |          |         |
    v          v         v
+-------+  +------+  +--------+
| Web   |  | API  |  |Resources|
| 🌐    |  | 🔗   |  | 💾      |
+-------+  +------+  +--------+
    |          |
    v          v
 Cache        DB
```

## Event Flow (Startup Sequence)

{event_diagram}

## Services

| Name | Class | Type |
|------|-------|------|
{service_rows if service_rows else "| — | — | — |"}

## Resources

| Name | Type | Role |
|------|------|------|
{resource_rows if resource_rows else "| — | — | — |"}

## API Endpoints

| Method | Path | Source |
|--------|------|--------|
{endpoint_rows if endpoint_rows else "| — | — | — |"}

## Scraping Summary

| Property | Value |
|----------|-------|
| Files scanned | {scrape_summary.get("file_count", "—")} |
| Timestamp | {scrape_summary.get("timestamp", timestamp)} |
| Services detected | {len(metadata["services"])} |
| Resources detected | {len(metadata["resources"])} |
| Endpoints detected | {len(metadata["endpoints"])} |

## Technology Stack

- **.NET Aspire** — distributed application orchestration
- **Blazor / Minimal API** — frontend and backend services
- **Redis** — output caching
- **SQL Server** — persistent storage
- **Python** — scraping and pipeline automation
- **Mermaid** — architecture and event-flow visualisation
- **MCP Agents** — intelligent documentation enrichment

---

*Generated automatically by `pipeline.py` on {timestamp}*
"""


# ---------------------------------------------------------------------------
# Pipeline orchestration
# ---------------------------------------------------------------------------

def run_pipeline(project_dir: str, urls: list, output_dir: str) -> bool:
    """Execute the full documentation pipeline."""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"\n{'='*60}")
    print(f"🚀 AgentCamp Documentation Pipeline")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"{'='*60}\n")

    # --- Step 1: Scrape ---
    print("📡 Step 1/3 — Scraping project files…")
    project_path = str(_ROOT / project_dir)
    project_files = scrape_project_files(project_path) if os.path.isdir(project_path) else []
    metadata = extract_aspire_metadata(project_files)

    scrape_summary = {
        "file_count": len(project_files),
        "timestamp": datetime.now().isoformat(),
    }

    raw_results = [{"type": "project_scan", **scrape_summary, "metadata": metadata}]

    # Optionally scrape remote URLs
    for url in urls:
        print(f"🌐 Scraping URL: {url}")
        raw_results.append(scrape_url(url))

    # Save raw scrape data
    scrape_output = str(_ROOT / output_dir / "scrape-results.json")
    save_scrape_results(raw_results, scrape_output)

    # --- Step 2: Analyze ---
    print(f"\n🔍 Step 2/3 — Analyzing architecture…")
    print(f"   Services  : {[s['name'] for s in metadata['services']]}")
    print(f"   Resources : {[r['name'] for r in metadata['resources']]}")
    print(f"   Endpoints : {len(metadata['endpoints'])}")

    # --- Step 3: Generate ---
    print(f"\n📝 Step 3/3 — Generating documentation…")
    docs = generate_documentation(metadata, scrape_summary, timestamp)

    out_dir = _ROOT / output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"SolutionOverview-{timestamp}.md"
    out_file.write_text(docs, encoding="utf-8")

    print(f"\n✅ Documentation saved to: {out_file}")
    print(f"{'='*60}\n")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="AgentCamp documentation pipeline: scrape → analyze → generate Mermaid docs"
    )
    parser.add_argument(
        "--project-dir", default="src",
        help="Relative path to the project source directory (default: src)"
    )
    parser.add_argument(
        "--url", action="append", default=[],
        help="Remote URL(s) to scrape (can be repeated; respects robots.txt)"
    )
    parser.add_argument(
        "--output-dir", default="docs",
        help="Output directory for generated documentation (default: docs)"
    )
    args = parser.parse_args()

    success = run_pipeline(args.project_dir, args.url, args.output_dir)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
