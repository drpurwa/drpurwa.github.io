using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using SnomedNlpBlazorApp.Models; // Ensure this namespace matches your Models folder
using System.Collections.Generic;
using System;

namespace SnomedNlpBlazorApp.Services
{
    public class GeminiService
    {
        private readonly HttpClient _httpClient;
        // IMPORTANT: For client-side Blazor WebAssembly, this API key will be visible in browser's dev tools.
        // For production, use a backend proxy to protect your API key.
        private readonly string _apiKey = "YOUR_GEMINI_API_KEY_HERE"; // REPLACE WITH YOUR ACTUAL GEMINI API KEY

        public GeminiService(HttpClient httpClient)
        {
            _httpClient = httpClient;
        }

        public async Task<List<ExtractedEntity>> ExtractEntities(string clinicalText)
        {
            var apiUrl = $"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={_apiKey}";

            // Define the structured response schema for Gemini
            var responseSchema = new
            {
                type = "ARRAY",
                items = new
                {
                    type = "OBJECT",
                    properties = new
                    {
                        text = new { type = "STRING", description = "The exact clinical term extracted from the text." },
                        snomedCode = new { type = "STRING", description = "The most appropriate SNOMED CT code (SCTID) for the concept. Leave empty if unsure." },
                        preferredTerm = new { type = "STRING", description = "The SNOMED CT Preferred Term for the concept. Leave empty if unsure." },
                        semanticCategory = new { type = "STRING", @enum = new[] { "disorder", "finding", "procedure", "observable entity", "medicinal product" }, description = "The semantic category of the concept (e.g., disorder, finding, procedure, observable entity, medicinal product)." },
                        confidenceScore = new { type = "STRING", @enum = new[] { "High", "Medium", "Low" }, description = "Confidence in the accuracy of the extracted concept and its SNOMED mapping (High, Medium, or Low)." },
                        context = new { type = "STRING", @enum = new[] { "present", "absent", "unknown" }, description = "The context of the term (present, absent, or unknown)." },
                        laterality = new { type = "STRING", @enum = new[] { "left", "right", "bilateral", "N/A" }, description = "Laterality of the concept, if applicable (left, right, bilateral, or N/A)." },
                        severity = new { type = "STRING", @enum = new[] { "mild", "moderate", "severe", "N/A" }, description = "Severity of the concept, if applicable (mild, moderate, severe, or N/A)." },
                        singularForm = new { type = "STRING", description = "The singular form of the extracted term, if applicable." }
                    },
                    required = new[] { "text", "semanticCategory", "confidenceScore", "context" }
                }
            };

            // Prompt for Gemini to act as a medical terminology expert system
            var payload = new
            {
                contents = new[]
                {
                    new
                    {
                        role = "user",
                        parts = new[]
                        {
                            new { text = $@"Anda adalah sistem pakar terminologi medis khusus yang dirancang untuk mengonversi narasi klinis berbahasa Indonesia menjadi kode SNOMED CT. Tugas Anda adalah menganalisis teks medis dan mengekstrak konsep klinis utama, lalu memetakannya ke kode SNOMED CT yang paling sesuai. Fokus pada identifikasi:
1. Diagnosis/kondisi (disorder)
2. Gejala dan temuan klinis (finding)
3. Prosedur yang dilakukan (procedure)
4. Entitas yang dapat diamati (observable entity)
5. Obat-obatan yang diberikan atau diresepkan (medicinal product)

Untuk setiap konsep yang diidentifikasi, berikan:
- Kode SNOMED CT (snomedCode)
- Istilah Pilihan SNOMED CT (preferredTerm)
- Kategori semantik (semanticCategory: disorder, finding, procedure, observable entity, medicinal product)
- Skor kepercayaan (confidenceScore: High/Medium/Low)
- Konteks (context: present/absent/unknown)
- Lateralitas (laterality: left/right/bilateral/N/A)
- Tingkat keparahan (severity: mild/moderate/severe/N/A)
- Bentuk tunggal dari istilah yang diekstrak (singularForm)

Pertahankan akurasi klinis dan utamakan spesifisitas daripada generalitas saat memilih kode.

Teks klinis: ""{clinicalText}""
" }
                        }
                    }
                },
                generationConfig = new
                {
                    responseMimeType = "application/json",
                    responseSchema = responseSchema,
                    temperature = 0.2
                }
            };

            try
            {
                var response = await _httpClient.PostAsJsonAsync(apiUrl, payload);
                response.EnsureSuccessStatusCode(); // Throws an exception if the HTTP response status is an error code

                var result = await response.Content.ReadFromJsonAsync<GeminiApiResponse>();

                if (result?.Candidates != null && result.Candidates.Count > 0 &&
                    result.Candidates[0]?.Content?.Parts != null && result.Candidates[0].Content.Parts.Count > 0)
                {
                    var jsonString = result.Candidates[0].Content.Parts[0].Text;
                    return System.Text.Json.JsonSerializer.Deserialize<List<ExtractedEntity>>(jsonString, new System.Text.Json.JsonSerializerOptions { PropertyNameCaseInsensitive = true });
                }
                throw new Exception("Unexpected response structure from Gemini API.");
            }
            catch (HttpRequestException ex)
            {
                Console.WriteLine($"Request error: {ex.Message}");
                throw new Exception($"Gagal terhubung ke Gemini API: {ex.Message}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error processing Gemini API response: {ex.Message}");
                throw new Exception($"Kesalahan saat memproses respons Gemini API: {ex.Message}");
            }
        }
    }
}
