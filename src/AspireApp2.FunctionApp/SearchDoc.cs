using Azure;
using Azure.AI.OpenAI;
using Azure.Storage.Blobs;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Extensions.Mcp;
using Microsoft.Extensions.Logging;
using UglyToad.PdfPig;

namespace AspireApp2.FunctionApp
{


    public class SearchDoc
    {
        private ILogger<SearchDoc> _logger;
        private readonly BlobServiceClient _blobServiceClient;
        private readonly OpenAIClient _openAI;


        public SearchDoc(ILogger<SearchDoc> logger, BlobServiceClient blobServiceClient)
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

        [Function("SearchPdf")]
        public async Task<object> SearchPdfAsync(
            [McpToolTrigger("search_pdf", "Búsqueda semántica dentro de un PDF usando embeddings.")]
        ToolInvocationContext context,

            [McpToolProperty("fileName", "Nombre del PDF a procesar.")]
        string fileName,

            [McpToolProperty("query", "Texto a buscar.")]
        string query
        )
        {
            _logger.LogInformation("Búsqueda semántica '{query}' en PDF: {fileName}", query, fileName);

            // 1. Leer PDF desde Blob Storage
            var container = _blobServiceClient.GetBlobContainerClient("pdfs");
            var blob = container.GetBlobClient(fileName);

            if (!await blob.ExistsAsync())
                return new { error = $"El archivo {fileName} no existe." };

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

            // 5. Embedding de la query
            var queryEmbedding = await GetEmbedding(query);

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

            return new
            {
                file = fileName,
                query,
                results
            };
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

        private async Task<float[]> GetEmbedding(string text)
        {
            var model = Environment.GetEnvironmentVariable("OpenAIEmbeddingModel");

            var response = await _openAI.GetEmbeddingsAsync(
                new EmbeddingsOptions(model, new[] { text })
            );

            return response.Value.Data[0].Embedding.ToArray();
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


    }
}
