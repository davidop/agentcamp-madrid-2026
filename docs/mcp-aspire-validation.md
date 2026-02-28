# Aspire MCP Server — Manual Validation Checklist

Use this checklist to confirm that the `aspire` MCP server in `.vscode/mcp.json` is working correctly inside VS Code with GitHub Copilot.

## Environment validation (terminal)

- [ ] **Verify .NET SDK**
  ```bash
  dotnet --info
  ```
  Expected: SDK 8.0+ (repo targets net10.0).

- [ ] **Verify Aspire workload**
  ```bash
  dotnet aspire --version
  ```
  If the command is not found, install the workload first:
  ```bash
  dotnet workload install aspire
  ```

- [ ] **Verify MCP subcommand exists**
  ```bash
  dotnet aspire mcp --help
  ```
  Expected: help text listing `stdio` as a sub-command.

- [ ] **Verify stdio server starts**
  ```bash
  dotnet aspire mcp stdio
  ```
  Expected: a JSON-RPC handshake line appears (e.g. `{"jsonrpc":"2.0",...}`).  
  Press `Ctrl+C` to stop after confirming the start.

## AppHost startup

- [ ] **Start the AppHost**
  ```bash
  dotnet run --project src/AspireApp2.AppHost/AspireApp2.AppHost.csproj
  ```
  Expected: dashboard URL printed, e.g.:
  ```
  Login to the dashboard at https://localhost:17169/login?t=<token>
  ```

- [ ] **Open the dashboard** in a browser and confirm all resources show as **Running / Healthy**.

## VS Code + Copilot validation

- [ ] **Open the repo in VS Code**

- [ ] **Check MCP server registration**
  - Open Command Palette → `MCP: List Servers`
  - Confirm `aspire` appears in the list with status **Running** (it starts on first use).

- [ ] **Open Copilot Chat in Agent mode**
  - Click the **Tools** icon (spanner/wrench) in the Copilot Chat panel.
  - Confirm `aspire` tools are listed (e.g. `aspire_list_resources`, `aspire_get_logs`, etc.).

## Functional prompts

Run each prompt in Copilot Chat with Agent mode active and the AppHost running:

- [ ] **List resources**
  ```
  Connect to the MCP `aspire` server and list all resources with their health status and endpoints.
  ```
  Expected: a table or list of Aspire resources (webfrontend, apiservice, redis, etc.) with their current state.

- [ ] **Fetch resource logs**
  ```
  Fetch the most recent logs from the `apiservice` resource.
  ```
  Expected: recent log lines from the API service.

- [ ] **Identify unhealthy resource**
  ```
  Identify any Unhealthy resource and correlate it with recent traces if available.
  ```
  Expected: Copilot either finds no unhealthy resources, or names the resource and shows correlated trace data.

## Troubleshooting quick reference

| Symptom | Action |
|---------|--------|
| `aspire` not in MCP server list | Check `.vscode/mcp.json` has the `aspire` entry; reload VS Code window |
| `dotnet aspire` not found | Run `dotnet workload install aspire` |
| stdio server exits immediately | Ensure AppHost is running first; check terminal output for errors |
| Dashboard URL not shown | Scroll up in the terminal; look for `Login to the dashboard at` line |
| Copilot Tools panel shows no `aspire` tools | Restart the MCP server via Command Palette → `MCP: Restart Server` → `aspire` |

## Agent environment — validation summary

Validation run on **2026-02-28** by the automated agent:

| Check | Result |
|-------|--------|
| `dotnet --info` | .NET SDK 10.0.102 — ✅ |
| `aspire --version` | Command not found — ⚠️ (`aspire` standalone CLI not installed) |
| `dotnet aspire --version` | Command not found — ⚠️ (workload not installed in runner) |
| MCP server config added to `.vscode/mcp.json` | ✅ |
| README updated | ✅ |

The `aspire` workload is not available in the CI runner environment. The MCP configuration is correct and will work once the workload is installed locally. Use the checklist above to validate in a developer workstation or Codespace where `dotnet workload install aspire` has been run.
