using AspireApp2.FunctionApp.Models;
using Azure;
using Azure.AI.OpenAI;
using Azure.Storage.Blobs;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Extensions.Logging;
using System.Text.Json;
using UglyToad.PdfPig;

namespace AspireApp2.FunctionApp
{


    public class TestOpenAI
    {
        private readonly ILogger<TestOpenAI> _logger;
        private readonly BlobServiceClient _blobServiceClient;
        private readonly OpenAIClient _openAI;

        public TestOpenAI(ILogger<TestOpenAI> logger, BlobServiceClient blobServiceClient)
        {
            _logger = logger;

            _blobServiceClient = blobServiceClient;

            var endpoint = Environment.GetEnvironmentVariable("OpenAIEndpoint");
            var key = Environment.GetEnvironmentVariable("OpenAIKey");

            if (string.IsNullOrEmpty(endpoint))
                throw new InvalidOperationException("OpenAIEndpoint environment variable is not set.");

            if (string.IsNullOrEmpty(key))
                throw new InvalidOperationException("OpenAIKey environment variable is not set.");

            _openAI = new OpenAIClient(
                new Uri(endpoint),
                new AzureKeyCredential(key)
            );
        }

        [Function("TestOpenAI")]
        public async Task<IActionResult> Run([HttpTrigger(AuthorizationLevel.Function, "post")] HttpRequest req)
        {
            _logger.LogInformation("C# HTTP trigger function processed a request.");

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();

            var fileName = "nopCommerce.pdf";

            var data = JsonSerializer.Deserialize<RequestModel>(requestBody);

            if (data == null || string.IsNullOrEmpty(data.Text))
            {
                return new BadRequestObjectResult("El JSON debe incluir { \"text\": \"...\" }");
            }

            string texto = data.Text;

            var container = _blobServiceClient.GetBlobContainerClient("docs");
            var blob = container.GetBlobClient(fileName);

            if (!await blob.ExistsAsync())
                return new NotFoundObjectResult(new { error = $"El archivo {fileName} no existe." });

            using var stream = new MemoryStream();
            await blob.DownloadToAsync(stream);
            stream.Position = 0;

            // 2. Extraer texto
            var pages = new List<string>();
            using (var doc = PdfDocument.Open(stream))
            {
                foreach (var page in doc.GetPages())
                    pages.Add(page.Text);
            }

            // 3. Chunking
            var chunks = ChunkText(string.Join("\n", pages), 8000);

            // 4. Embeddings de chunks
            var chunkEmbeddings = new List<(string chunk, float[] vector)>();
            foreach (var chunk in chunks)
            {
                var emb = await GetEmbedding(chunk);
                chunkEmbeddings.Add((chunk, emb));
            }

            var queryEmbedding = await GetEmbedding(data.Text);

            // 6. Calcular similitud coseno
            var results = chunkEmbeddings
                .Select(c => new
                {
                    c.chunk,
                    score = CosineSimilarity(queryEmbedding, c.vector)
                })
                .OrderByDescending(r => r.score)
                .Take(5)
                .ToList();

            //return new
            //{
            //    file = fileName,
            //    data.Text,
            //    results
            //};

            return new OkObjectResult(results);
        }

        private List<string> ChunkText(string text, int size)
        {
            var chunks = new List<string>();
            for (int i = 0; i < text.Length; i += size)
            {
                chunks.Add(text.Substring(i, Math.Min(size, text.Length - i)));
            }
            return chunks;
        }


        private double CosineSimilarity(float[] a, float[] b)
        {
            double dot = 0, magA = 0, magB = 0;
            for (int i = 0; i < a.Length; i++)
            {
                dot += a[i] * b[i];
                magA += a[i] * a[i];
                magB += b[i] * b[i];
            }
            return dot / (Math.Sqrt(magA) * Math.Sqrt(magB));
        }


        private async Task<float[]> GetEmbedding(string text)
        {
            var model = Environment.GetEnvironmentVariable("OpenAIEmbeddingModel");

            var response = await _openAI.GetEmbeddingsAsync(
                new EmbeddingsOptions(model, new[] { text })
            );

            return response.Value.Data[0].Embedding.ToArray();
        }
    }
}