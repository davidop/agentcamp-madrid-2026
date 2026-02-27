# Agents Overview

This folder contains custom GitHub Copilot agent prompts for .NET Aspire solutions.

## Available Agents

### Documentation Agents

- **`aspire-solution-documenter-mermaid.md`**
  - Analyzes and documents .NET Aspire solutions with comprehensive architecture analysis
  - Supports ASCII diagrams, Mermaid charts (via MCP), or both formats
  - Optional screenshots via Playwright MCP
  - Generates detailed markdown documentation in `docs/`

### Infrastructure Agents

- **`azure-bicep-infrastructure.md`**
  - Specialized in Azure Infrastructure as Code using Bicep
  - Analyzes Aspire AppHost and generates complete Azure deployment templates
  - Creates modular Bicep files for Container Apps, SQL, Redis, Key Vault, etc.
  - Includes deployment scripts, parameters files, and comprehensive documentation
  - Supports multi-environment configurations (dev/staging/prod)

## When To Use Each Agent

### Documentation Agent (Mermaid Variant)
**Use when you need:**
- Complete solution analysis and documentation
- Architecture diagrams in ASCII or Mermaid format
- Visual representation of services, dependencies, and infrastructure
- Screenshots of Aspire Dashboard and frontend
- Detailed component descriptions and technical specifications

**Prerequisites:**
- .NET 9 SDK
- Docker Desktop (for running the solution)
- MCP Mermaid server (for diagram rendering)
- MCP Playwright (optional, for screenshots)

### Azure Bicep Infrastructure Agent
**Use when you need:**
- Deploy Aspire application to Azure
- Generate Infrastructure as Code templates
- Create production-ready Azure resources
- Set up Container Apps, databases, caching, monitoring
- Multi-environment deployment configurations
- Cost-optimized Azure architecture

**Prerequisites:**
- Azure CLI installed and authenticated
- Azure subscription with appropriate permissions
- Docker for building and pushing container images
- Understanding of Azure services and pricing

## Output Locations

### Documentation Agent
- **Documentation:** `docs/SolutionOverview-yyyyMMdd-hhmmss.md`
- **Mermaid diagrams:** `docs/diagrams/architecture-YYYYMMDD-hhmmss.png`
- **Screenshots:** `docs/screenshots/`

### Infrastructure Agent
- **Bicep templates:** `/infra/bicep/main.bicep` and modules
- **Parameters:** `/infra/bicep/main.parameters.json`
- **Scripts:** `/infra/bicep/scripts/` (deploy.ps1, build-and-push.ps1)
- **Documentation:** `/infra/bicep/README.md`

## Typical Workflows

### Workflow 1: Document Existing Solution
1. Ensure Docker is running and Aspire solution is launched
2. Use **Documentation Agent** with Mermaid option
3. Agent analyzes all projects, generates diagram, creates comprehensive docs
4. Review generated documentation in `docs/`

### Workflow 2: Deploy to Azure
1. Use **Documentation Agent** first to understand the architecture
2. Use **Azure Bicep Infrastructure Agent** to generate IaC templates
3. Review and customize generated Bicep modules and parameters
4. Run deployment scripts to provision Azure resources
5. Build and push Docker images to Azure Container Registry
6. Deploy Container Apps with the infrastructure

### Workflow 3: Full Lifecycle
1. **Document:** Generate solution documentation with diagrams
2. **Develop:** Make changes to your Aspire application
3. **Test:** Run locally with Docker containers
4. **Deploy:** Use Bicep templates to deploy to Azure dev environment
5. **Promote:** Use same templates with prod parameters for production
6. **Monitor:** Use Application Insights and Log Analytics configured by Bicep

## Troubleshooting

### Documentation Agent
- **Dashboard HTTPS warning:** If `https://localhost:17187` fails due to cert issues, try HTTP port from AppHost `launchSettings.json` (e.g., `http://localhost:15273`)
- **Docker not running:** Ensure Docker Desktop is running so Redis/SQL containers can start
- **Mermaid rendering fails:** Verify `mcp-mermaid` server is configured and reachable
- **Screenshot failures:** Verify `mcp-playwright` is installed and can access app URLs

### Infrastructure Agent
- **Azure CLI not found:** Install Azure CLI from https://aka.ms/installazurecli
- **Authentication errors:** Run `az login` and verify subscription with `az account show`
- **Deployment fails:** Check `az deployment group what-if` for validation before actual deployment
- **Permission issues:** Ensure you have Contributor role on the subscription or resource group
- **Cost concerns:** Review generated cost estimates and adjust SKUs in parameters file

## Best Practices

### For Documentation
- Run documentation agent after significant architecture changes
- Keep diagrams updated as services evolve
- Use Mermaid for presentations and reports
- Store documentation in version control alongside code

### For Infrastructure
- Start with dev environment, validate, then promote to production
- Use separate parameter files for each environment
- Store secrets in Azure Key Vault, never in code
- Tag all resources with environment, owner, and cost center
- Enable monitoring and alerting from day one
- Review cost optimization recommendations regularly

## Getting Help

For issues or questions:
- Review the individual agent markdown files for detailed instructions
- Check Azure Bicep documentation: https://learn.microsoft.com/azure/azure-resource-manager/bicep/
- Check .NET Aspire docs: https://learn.microsoft.com/dotnet/aspire/
- Review generated README.md files for specific guidance
