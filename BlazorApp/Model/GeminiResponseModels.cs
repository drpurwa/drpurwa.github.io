using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace SnomedNlpBlazorApp.Models
{
    // These classes are designed to match the JSON structure returned by the Gemini API
    // based on the defined responseSchema.

    public class GeminiApiResponse
    {
        [JsonPropertyName("candidates")]
        public List<Candidate>? Candidates { get; set; }
    }

    public class Candidate
    {
        [JsonPropertyName("content")]
        public Content? Content { get; set; }
    }

    public class Content
    {
        [JsonPropertyName("parts")]
        public List<Part>? Parts { get; set; }

        [JsonPropertyName("role")]
        public string? Role { get; set; }
    }

    public class Part
    {
        [JsonPropertyName("text")]
        public string? Text { get; set; }
    }

    // This class represents the structured entity extracted by Gemini,
    // as defined in the responseSchema's 'items' properties.
    public class ExtractedEntity
    {
        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        [JsonPropertyName("snomedCode")]
        public string SnomedCode { get; set; } = string.Empty;

        [JsonPropertyName("preferredTerm")]
        public string PreferredTerm { get; set; } = string.Empty;

        [JsonPropertyName("semanticCategory")]
        public string SemanticCategory { get; set; } = string.Empty;

        [JsonPropertyName("confidenceScore")]
        public string ConfidenceScore { get; set; } = string.Empty;

        [JsonPropertyName("context")]
        public string Context { get; set; } = string.Empty;

        [JsonPropertyName("laterality")]
        public string Laterality { get; set; } = string.Empty;

        [JsonPropertyName("severity")]
        public string Severity { get; set; } = string.Empty;

        [JsonPropertyName("singularForm")]
        public string SingularForm { get; set; } = string.Empty;
    }
}
