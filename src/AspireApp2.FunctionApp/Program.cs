using Azure.Storage.Blobs;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;


var builder = FunctionsApplication.CreateBuilder(args);

// Habilita el servidor MCP
builder.ConfigureFunctionsWebApplication();

// Telemetría opcional
builder.Services
    .AddApplicationInsightsTelemetryWorkerService()
    .ConfigureFunctionsApplicationInsights();

// Registrar BlobServiceClient usando una variable de entorno
builder.Services.AddSingleton(sp =>
{
    var connectionString = Environment.GetEnvironmentVariable("BlobConnection");

    if (string.IsNullOrEmpty(connectionString))
        throw new InvalidOperationException("La variable BlobConnection no está configurada.");

    return new BlobServiceClient(connectionString);
});

builder.Build().Run();
