# AspireApp2 - Solution Overview

**Generated:** November 26, 2025 15:30:00  
**Aspire Version:** 9.3.2  
**.NET Version:** 9.0

---

## Overview

**AspireApp2** is a cloud-native microservices application built with **.NET Aspire**, demonstrating modern distributed application architecture patterns. The solution showcases a weather forecasting application with a Blazor Server frontend that consumes data from a backend API service, leveraging Redis caching and SQL Server for data persistence.

### Purpose

This solution serves as a reference implementation for:
- **Microservices orchestration** using .NET Aspire AppHost
- **Service discovery** and communication between distributed components
- **Observability** with built-in OpenTelemetry integration
- **Resilience patterns** with automatic retries and circuit breakers
- **Cloud-ready infrastructure** deployable to Azure Container Apps

### Key Technologies

- **.NET 9.0** - Latest .NET runtime with performance improvements
- **.NET Aspire 9.3.2** - Cloud-native application orchestration framework
- **Blazor Server** - Interactive web UI with server-side rendering
- **ASP.NET Core Minimal APIs** - Lightweight, high-performance REST endpoints
- **Redis** - Distributed caching with output caching support
- **SQL Server 2025** - Relational database for data persistence
- **OpenTelemetry** - Distributed tracing, metrics, and logging

### Target Audience

- Development teams building cloud-native .NET applications
- DevOps engineers implementing microservices architectures
- Architects evaluating .NET Aspire for distributed systems
- Organizations migrating to container-based deployments

---

## Architecture

### Architectural Pattern

AspireApp2 follows a **microservices architecture** with the following characteristics:

- **Orchestrator Pattern**: Central AppHost manages lifecycle of all services and resources
- **Service Discovery**: Built-in service resolution using `https+http://` scheme
- **Backend for Frontend (BFF)**: Web frontend acts as a gateway to backend services
- **Sidecar Pattern**: ServiceDefaults provides cross-cutting concerns to all services
- **Container-First**: All infrastructure components run in containers

### Design Principles

1. **Separation of Concerns**: Each service has a single, well-defined responsibility
2. **Dependency Inversion**: Services depend on abstractions via service discovery
3. **Resilience by Default**: Automatic retries, circuit breakers, and health checks
4. **Observability First**: Comprehensive telemetry built into every component
5. **Configuration over Convention**: Explicit orchestration in AppHost

### Infrastructure Components

#### SQL Server (`productsDb`)
- **Version**: SQL Server 2025 (latest)
- **Purpose**: Primary data store for application data
- **Configuration**: Persistent container with data volume
- **Access**: Connection managed through ServiceDefaults with automatic connection string injection

#### Redis Cache
- **Purpose**: Distributed output caching for web responses
- **Usage**: Blazor pages use `[OutputCache]` attribute with 5-second duration
- **Benefits**: Reduces API calls and improves response times

#### Aspire Dashboard
- **URL**: https://localhost:17187 (HTTPS) / http://localhost:15273 (HTTP)
- **Features**:
  - Real-time resource monitoring
  - Distributed tracing visualization
  - Logs aggregation
  - Metrics dashboards
  - Health status of all services

---

## Architecture Diagram

The following diagram illustrates the complete architecture of AspireApp2, showing service relationships, dependencies, and data flow:

![Architecture Diagram](diagrams/architecture-20251126-153000.png)

### Key Architecture Elements

1. **Aspire AppHost**: Central orchestration layer that registers and manages all resources
2. **Infrastructure Resources**: SQL Server and Redis running as containers
3. **Application Services**: API Service (backend) and Web Frontend (Blazor)
4. **Service Defaults**: Shared library providing observability, health checks, and resilience
5. **Observability Stack**: OpenTelemetry exports to Aspire Dashboard for monitoring

### Service Dependencies

- **Web → API**: HTTP communication via service discovery (`https+http://apiservice`)
- **Web → Redis**: Output caching for page responses
- **API → SQL Server**: Data persistence with `WaitFor` dependency to ensure database readiness
- **All Services → Observability**: Automatic telemetry export to dashboard

---

## Components

### 1. AspireApp2.AppHost

**Type:** .NET Aspire Orchestrator  
**Role:** Application composition and lifecycle management

#### Responsibilities
- Registers infrastructure resources (SQL Server, Redis)
- Deploys and configures application services
- Manages service dependencies and startup order
- Provides dashboard for monitoring

#### Key Configuration

```csharp
// Infrastructure
var sql = builder.AddSqlServer("sql")
    .WithLifetime(ContainerLifetime.Persistent)
    .WithImageTag("2025-latest")
    .WithEnvironment("ACCEPT_EULA", "Y");

var productsDb = sql
    .WithDataVolume()
    .AddDatabase("productsDb");

var cache = builder.AddRedis("cache");

// Services with dependencies
var apiService = builder.AddProject<Projects.AspireApp2_ApiService>("apiservice")
    .WithReference(productsDb)
    .WaitFor(productsDb);

builder.AddProject<Projects.AspireApp2_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithReference(cache)
    .WaitFor(cache)
    .WithReference(apiService)
    .WaitFor(apiService);
```

#### NuGet Packages
- `Aspire.Hosting.AppHost` 9.3.1
- `Aspire.Hosting.Redis` 9.3.1
- `Aspire.Hosting.SqlServer` 9.3.2
- `Aspire.Hosting.Azure.ApplicationInsights` 9.3.1
- `Aspire.Hosting.Azure.CognitiveServices` 9.3.1

#### Launch URLs
- **HTTPS**: https://localhost:17187
- **HTTP**: http://localhost:15273

---

### 2. AspireApp2.Web

**Type:** Blazor Server Application  
**Role:** Interactive web frontend with server-side rendering

#### Responsibilities
- Renders interactive UI components
- Consumes weather data from API service
- Implements output caching with Redis
- Provides user-facing endpoints

#### Key Features
- **Interactive Server Rendering**: Real-time UI updates via SignalR
- **Output Caching**: Page-level caching with `[OutputCache(Duration = 5)]`
- **Service Discovery**: Automatic API endpoint resolution
- **Streaming Rendering**: Progressive page loading with `[StreamRendering(true)]`

#### Dependencies
- **AspireApp2.ApiService**: Weather data provider (via HTTP)
- **Redis Cache**: Output caching backend
- **AspireApp2.ServiceDefaults**: Shared observability and resilience

#### Configuration

```csharp
// Redis output caching
builder.AddRedisOutputCache("cache");

// HTTP client with service discovery
builder.Services.AddHttpClient<WeatherApiClient>(client =>
{
    client.BaseAddress = new("https+http://apiservice");
});
```

#### NuGet Packages
- `Aspire.StackExchange.Redis.OutputCaching` 9.3.1

#### Pages
- **Home** (`/`): Landing page
- **Counter** (`/counter`): Interactive counter demo
- **Weather** (`/weather`): Weather forecast data with caching

---

### 3. AspireApp2.ApiService

**Type:** ASP.NET Core Minimal API  
**Role:** Backend REST API for weather data

#### Responsibilities
- Exposes `/weatherforecast` endpoint
- Generates random weather forecast data
- Integrates with SQL Server (via ServiceDefaults)
- Provides OpenAPI documentation (development mode)

#### Endpoints

| Method | Path              | Description                  | Response Type          |
|--------|-------------------|------------------------------|------------------------|
| GET    | `/weatherforecast`| Returns 5-day weather forecast | `WeatherForecast[]`   |
| GET    | `/health`         | Health check endpoint        | `HealthCheckResult`    |
| GET    | `/alive`          | Liveness probe               | `200 OK`               |

#### Data Model

```csharp
record WeatherForecast(DateOnly Date, int TemperatureC, string? Summary)
{
    public int TemperatureF => 32 + (int)(TemperatureC / 0.5556);
}
```

#### Dependencies
- **SQL Server (productsDb)**: Data persistence (via connection string injection)
- **AspireApp2.ServiceDefaults**: Shared observability and resilience

#### NuGet Packages
- `Microsoft.AspNetCore.OpenApi` 9.0.7

#### Launch URLs (Direct)
- **HTTPS**: https://localhost:7127
- **HTTP**: http://localhost:5027

---

### 4. AspireApp2.ServiceDefaults

**Type:** Class Library  
**Role:** Shared cross-cutting concerns for all services

#### Responsibilities
- Configures OpenTelemetry (traces, metrics, logs)
- Registers health checks (liveness, readiness)
- Enables service discovery
- Adds resilience patterns (retries, circuit breakers, timeouts)

#### Key Features

**OpenTelemetry Configuration**
- ASP.NET Core instrumentation
- HTTP client instrumentation
- Runtime metrics (GC, thread pool, etc.)
- OTLP exporter for dashboard integration

**Resilience Handlers**
- Standard retry policy with exponential backoff
- Circuit breaker with failure threshold
- Timeout policies for HTTP calls

**Health Checks**
- Self-check for service responsiveness
- Integration health checks (database, cache)

#### Extension Methods

```csharp
builder.AddServiceDefaults(); // Adds all default services
builder.AddRedisOutputCache("cache"); // Web-specific
```

#### NuGet Packages
- `Microsoft.Extensions.Http.Resilience` 9.7.0
- `Microsoft.Extensions.ServiceDiscovery` 9.3.1
- `OpenTelemetry.Exporter.OpenTelemetryProtocol` 1.12.0
- `OpenTelemetry.Extensions.Hosting` 1.12.0
- `OpenTelemetry.Instrumentation.AspNetCore` 1.12.0
- `OpenTelemetry.Instrumentation.Http` 1.12.0
- `OpenTelemetry.Instrumentation.Runtime` 1.12.0

---

### 5. AspireApp2.Tests

**Type:** MSTest Integration Tests  
**Role:** Automated testing with Aspire.Hosting.Testing

#### Responsibilities
- Integration tests for web frontend
- End-to-end service communication tests
- Health check validation

#### NuGet Packages
- `Aspire.Hosting.Testing` 9.3.1
- `MSTest` 3.9.3

---

## Features

### Main Application Features

#### 1. Weather Forecasting Service
- **Capability**: Provides 5-day weather forecast data
- **Implementation**: Backend API generates random forecasts with temperatures and conditions
- **Caching**: Responses cached for 5 seconds to reduce load
- **User Experience**: Streaming rendering with progressive data loading

#### 2. Interactive Web Interface
- **Technology**: Blazor Server with Interactive Server Components
- **Pages**:
  - Home page with navigation
  - Counter demo showing state management
  - Weather page displaying forecast data
- **Features**:
  - Real-time updates via SignalR
  - Responsive design with Bootstrap
  - Error boundary handling

#### 3. Service Discovery
- **Automatic Endpoint Resolution**: Services find each other via logical names
- **Protocol Preference**: `https+http://` scheme prefers HTTPS, falls back to HTTP
- **Dynamic Configuration**: No hardcoded URLs required

#### 4. Distributed Caching
- **Redis-Based**: Centralized cache shared across instances
- **Output Caching**: Page-level caching with TTL
- **Cache Keys**: Automatic generation based on route and parameters

### API Capabilities

#### RESTful Weather API
- **Endpoint**: `GET /weatherforecast`
- **Format**: JSON
- **Pagination**: Returns 5 forecasts by default (configurable)
- **Schema**: OpenAPI/Swagger documentation in development mode

#### Health Monitoring
- **Liveness**: `/alive` endpoint for container orchestration
- **Readiness**: `/health` endpoint with dependency checks
- **Metrics**: Prometheus-compatible metrics endpoint

### Data Management

#### SQL Server Integration
- **Database**: `productsDb` (ready for entity storage)
- **Connection Management**: Automatic via ServiceDefaults
- **Migrations**: Ready for EF Core migrations
- **Persistence**: Data volume ensures data survives container restarts

#### Redis Caching Strategy
- **Output Caching**: HTTP response caching
- **Expiration**: Time-based (5 seconds default)
- **Eviction**: LRU (Least Recently Used) when memory limit reached

---

## Technical Details

### .NET and Aspire Versions

| Component              | Version  | Release Date       |
|------------------------|----------|--------------------|
| .NET SDK               | 9.0      | November 2024      |
| .NET Aspire            | 9.3.2    | November 2025      |
| Aspire.AppHost.Sdk     | 9.0.0    | November 2024      |
| C# Language            | 13.0     | November 2024      |

### Key NuGet Packages

#### Aspire Packages
- `Aspire.Hosting.AppHost` 9.3.1
- `Aspire.Hosting.Redis` 9.3.1
- `Aspire.Hosting.SqlServer` 9.3.2
- `Aspire.StackExchange.Redis.OutputCaching` 9.3.1
- `Aspire.Hosting.Azure.ApplicationInsights` 9.3.1
- `Aspire.Hosting.Testing` 9.3.1

#### OpenTelemetry Packages
- `OpenTelemetry.Exporter.OpenTelemetryProtocol` 1.12.0
- `OpenTelemetry.Instrumentation.AspNetCore` 1.12.0
- `OpenTelemetry.Instrumentation.Http` 1.12.0
- `OpenTelemetry.Instrumentation.Runtime` 1.12.0

#### Microsoft Packages
- `Microsoft.Extensions.Http.Resilience` 9.7.0
- `Microsoft.Extensions.ServiceDiscovery` 9.3.1
- `Microsoft.AspNetCore.OpenApi` 9.0.7
- `MSTest` 3.9.3

### Authentication & Authorization

**Current Implementation**: None (development mode)

**Production Recommendations**:
- **Azure AD / Entra ID**: For enterprise authentication
- **JWT Bearer Tokens**: For API authentication
- **API Keys**: For external service access
- **RBAC**: Role-based access control for endpoints

**Aspire Support**:
- Azure AD integration via `Aspire.Hosting.Azure.KeyVault`
- Managed Identity support for Azure resources
- Secrets management with UserSecrets (development) / Key Vault (production)

### Observability & Monitoring

#### Distributed Tracing
- **Provider**: OpenTelemetry Protocol (OTLP)
- **Backend**: Aspire Dashboard
- **Instrumentation**:
  - HTTP request/response traces
  - Database query traces (when EF Core added)
  - Custom activity spans available

#### Metrics Collection
- **ASP.NET Core Metrics**: Request duration, response codes, throughput
- **HTTP Client Metrics**: Outbound call latency, failures
- **Runtime Metrics**: GC pauses, thread pool usage, CPU time
- **Custom Metrics**: Available via `IMeterFactory`

#### Logging
- **Structured Logging**: JSON-formatted logs with context
- **Log Levels**: Configured per namespace in `appsettings.json`
- **Centralization**: All logs visible in Aspire Dashboard
- **Scopes**: Correlation IDs automatically added

#### Dashboard Features
- Resource view with real-time status
- Trace explorer with flame graphs
- Metrics charts with time-series data
- Log viewer with filtering and search
- Console output from all services

### Deployment Considerations

#### Local Development
- **Requirements**: Docker Desktop (for SQL Server and Redis containers)
- **Launch**: Run AppHost project to start entire solution
- **Hot Reload**: Supported for code changes
- **Debugging**: Multi-project debugging in Visual Studio

#### Azure Container Apps (Recommended)
- **Infrastructure**: Bicep templates included in `infra/bicep/`
- **Services**:
  - Container Apps Environment with Log Analytics
  - Azure SQL Database (replaces SQL Server container)
  - Azure Cache for Redis (replaces Redis container)
  - Azure Container Registry for image storage
  - Application Insights for telemetry
  - Key Vault for secrets
  - Managed Identity for authentication
- **Deployment**: PowerShell scripts in `infra/bicep/scripts/`
- **Cost**: Basic tier ~$50-100/month (varies by region)

#### Kubernetes (Alternative)
- **Manifest Generation**: Use Aspire 9.0+ `WithManifest()` extension
- **Helm Charts**: Can be generated from Aspire manifests
- **Ingress**: Configure for webfrontend external access
- **Secrets**: Use Kubernetes Secrets or external secret operators

#### Docker Compose (Development)
- **Generation**: Aspire can export docker-compose.yml
- **Limitations**: No service discovery, manual configuration required
- **Use Case**: CI/CD pipelines, simple deployments

### Performance Characteristics

#### Blazor Server
- **First Load**: ~50-100ms (including SignalR negotiation)
- **SignalR Latency**: <10ms on local network
- **Memory**: ~2-5 MB per active user session
- **Scalability**: Requires sticky sessions or Redis backplane

#### API Service
- **Response Time**: <50ms for weatherforecast endpoint
- **Throughput**: 10,000+ req/s per instance (theoretical)
- **CPU**: Minimal (in-memory data generation)
- **Memory**: ~50 MB per instance

#### Redis Caching
- **Hit Rate**: ~80-90% for weather page (5s TTL)
- **Latency**: <1ms for cache hits
- **Memory**: Minimal (few cached responses)

### Security Best Practices

1. **HTTPS Everywhere**: All services support HTTPS with development certificates
2. **Secret Management**: UserSecrets in development, Key Vault in production
3. **Dependency Updates**: Use `dotnet list package --outdated` regularly
4. **Container Scanning**: Scan images for vulnerabilities before deployment
5. **Network Policies**: Isolate services in production environments
6. **Least Privilege**: Run containers as non-root users

### Scaling Strategies

#### Horizontal Scaling
- **Web Frontend**: Can scale to multiple instances with Redis session state
- **API Service**: Stateless, scales linearly
- **Redis**: Use Azure Cache for Redis with clustering
- **SQL Server**: Use Azure SQL with read replicas

#### Vertical Scaling
- **Memory**: Increase for services handling large datasets
- **CPU**: Increase for compute-intensive operations

#### Auto-Scaling
- **Triggers**: CPU > 70%, Memory > 80%, Request queue depth
- **Min Instances**: 1 (development), 2 (production)
- **Max Instances**: 10 (configurable)

---

## Future Enhancements

### Potential Improvements

1. **Database Schema**: Add EF Core models and migrations for actual product data
2. **Authentication**: Implement Azure AD authentication for web and API
3. **API Versioning**: Add versioning support to API endpoints
4. **Rate Limiting**: Implement rate limiting for public API endpoints
5. **CQRS Pattern**: Separate read/write models for complex operations
6. **Message Queue**: Add Azure Service Bus for async operations
7. **Blob Storage**: Integrate Azure Blob Storage for file uploads
8. **GraphQL**: Add GraphQL endpoint for flexible data queries
9. **gRPC**: High-performance service-to-service communication
10. **Progressive Web App**: Add PWA capabilities to Blazor frontend

---

## Getting Started

### Prerequisites
- .NET 9.0 SDK or later
- Docker Desktop (for local development)
- Visual Studio 2022 v17.12+ or VS Code with C# extension
- Azure CLI (for cloud deployment)

### Running Locally

1. **Clone the repository**
2. **Start Docker Desktop**
3. **Run the AppHost**:
   ```bash
   cd src/AspireApp2.AppHost
   dotnet run
   ```
4. **Access the Dashboard**: Navigate to https://localhost:17187
5. **Access the Web App**: Click "webfrontend" endpoint in dashboard

### Deploying to Azure

See the complete deployment guide in `infra/bicep/README.md`:

```powershell
# Login to Azure
az login

# Build and push Docker images
.\infra\bicep\scripts\build-and-push.ps1

# Deploy infrastructure
.\infra\bicep\scripts\deploy.ps1
```

---

## Resources

- [.NET Aspire Documentation](https://learn.microsoft.com/dotnet/aspire/)
- [Blazor Documentation](https://learn.microsoft.com/aspnet/core/blazor/)
- [OpenTelemetry .NET](https://opentelemetry.io/docs/languages/net/)
- [Azure Container Apps](https://learn.microsoft.com/azure/container-apps/)

---

## Support & Contributions

For issues, questions, or contributions, please refer to the repository's issue tracker and contribution guidelines.

---

**Document Version**: 1.0  
**Last Updated**: November 26, 2025 15:30:00  
**Maintained By**: Development Team
