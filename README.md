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

The `.vscode/mcp.json` file configures the following MCP servers for VS Code Copilot:

| Server | Purpose |
|--------|---------|
| `playwright` | Browser automation and screenshot capture |
| `mcp-mermaid` | Mermaid diagram rendering and validation |
| `remote-mcp-azure-function` | Azure Function–hosted MCP server (requires key) |
| `github-agentic-workflows` | GitHub agentic workflows via `gh` CLI |
| `aspire` | Exposes running Aspire resources, health status, logs, and traces to Copilot |

### Aspire MCP Server

The `aspire` server lets GitHub Copilot interact with your running .NET Aspire application directly from VS Code Chat. It provides:

- **Resource listing** — see all Aspire services and their current state/endpoints
- **Health status** — identify Unhealthy or Degraded resources at a glance
- **Logs** — fetch recent log output for any running resource
- **Traces** — correlate distributed traces across microservices

#### Prerequisites

- [.NET Aspire workload](https://learn.microsoft.com/dotnet/aspire/fundamentals/setup-tooling) (`dotnet workload install aspire`) — provides the `dotnet aspire` global tool
- AppHost running locally (`dotnet run --project src/AspireApp2.AppHost/AspireApp2.AppHost.csproj`)
- GitHub Copilot extension in VS Code with **Agent mode** enabled

#### Quick start

1. Start the AppHost:
   ```bash
   dotnet run --project src/AspireApp2.AppHost/AspireApp2.AppHost.csproj
   ```
2. Open VS Code → **Copilot Chat** → click **Tools** → confirm `aspire` appears in the list.
3. In Copilot Chat (Agent mode) try:
   ```
   List all Aspire resources with their health status and endpoints.
   ```

## Troubleshooting

### `aspire` command not found / `dotnet aspire` not found

The Aspire CLI ships as part of the `aspire` .NET workload. Install it with:

```bash
dotnet workload install aspire
```

After installation, verify:

```bash
dotnet aspire --version
```

### Verify that the MCP server starts

Run the stdio server manually and check for a clean start:

```bash
dotnet aspire mcp stdio
```

A successful start prints a JSON-RPC handshake line. Any error here (e.g. "AppHost not running") must be resolved before VS Code can use the tool.

### Locating the Aspire Dashboard URL

When the AppHost starts it prints a line such as:

```
Login to the dashboard at https://localhost:17169/login?t=<token>
```

Copy that URL into your browser to inspect resources, logs, and traces visually.

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


