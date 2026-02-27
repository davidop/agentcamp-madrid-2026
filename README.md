# CopilotAspireArchitectureGeneration

Sample code to show how to generate an architecture diagram from a .NET Aspire solution using different prompt approaches, combined with Python scraping and MCP Agents for a fully automated documentation pipeline.

<img width="2610" height="1672" alt="image" src="https://github.com/user-attachments/assets/4e0bae37-fe7d-4742-bbe0-934fab2cceda" />

## What this demo covers

This repository demonstrates the concepts presented at **AgentCamp Madrid 2026**:

- 🔷 **.NET Aspire** — microservices orchestration (AppHost, Web, ApiService, ServiceDefaults)
- 🤖 **MCP Agents** — intelligent documentation enrichment via the `mcp-mermaid` and Playwright servers
- 🐍 **Python scraping** — controlled extraction of project and documentation information
- 📊 **Mermaid visualisation** — architecture diagrams, event flows, and pipeline charts

The full pipeline goes from **raw code** → **scraped metadata** → **AI-generated documentation with Mermaid diagrams**.

## Pipeline

```
scraper.py  ──►  extract_aspire_metadata  ──►  pipeline.py  ──►  docs/SolutionOverview-*.md
                                                    │
                                             MCP Agent review
```

## Quick start

### 1. Run the documentation pipeline

```bash
python pipeline.py
```

This will:
1. Scan all source files under `src/`
2. Extract Aspire services, resources, and API endpoints
3. Generate `docs/SolutionOverview-<timestamp>.md` with:
   - Architecture diagram (Mermaid `graph TB`)
   - Event flow diagram (Mermaid `sequenceDiagram`)
   - Pipeline diagram (Mermaid `flowchart`)

Optional — also scrape a remote URL:

```bash
python pipeline.py --url https://learn.microsoft.com/en-us/dotnet/aspire/get-started/aspire-overview
```

### 2. Run only the scraper

```bash
python scraper.py
python scraper.py --url https://example.com/docs
```

### 3. Generate docs with Mermaid charts (original script)

```bash
python generate_mermaid_docs.py
```

### 4. Validate generated Mermaid syntax

```bash
python validate_mermaid.py
```

### 5. Launch the .NET Aspire solution

```bash
dotnet run --project src/AspireApp2.AppHost/AspireApp2.AppHost.csproj
```

## MCP Servers

The `src/.mcp.json` file configures the following MCP servers:

| Server | Purpose |
|--------|---------|
| `playwright` | Browser automation and screenshot capture |
| `mcp-mermaid` | Mermaid diagram rendering and validation |
| `hf-mcp-server` | Hugging Face model access (requires token) |

## Repository structure

```
├── src/                        # .NET Aspire solution
│   ├── AspireApp2.AppHost/     # Orchestrator
│   ├── AspireApp2.Web/         # Blazor frontend
│   ├── AspireApp2.ApiService/  # Weather API
│   ├── AspireApp2.ServiceDefaults/
│   └── AspireApp2.Tests/
├── docs/                       # Generated documentation
│   └── diagrams/               # Architecture diagram images
├── scraper.py                  # Python scraping module
├── pipeline.py                 # Documentation pipeline orchestrator
├── generate_mermaid_docs.py    # Mermaid chart generation script
├── validate_mermaid.py         # Mermaid syntax validator
├── prompt-generatedoc.md       # Agent prompt (ASCII diagrams)
└── prompt-generatedoc-mermaidcharts.md  # Agent prompt (Mermaid charts)
```


