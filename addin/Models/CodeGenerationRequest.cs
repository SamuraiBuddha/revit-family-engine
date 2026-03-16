using Newtonsoft.Json;

namespace RevitFamilyEngine.Models;

public class CodeGenerationRequest
{
    [JsonProperty("prompt")]
    public string Prompt { get; set; } = string.Empty;

    [JsonProperty("domain")]
    public string Domain { get; set; } = "family_geometry";

    [JsonProperty("context")]
    public string? Context { get; set; }

    [JsonProperty("include_comments")]
    public bool IncludeComments { get; set; } = true;

    [JsonProperty("model")]
    public string? Model { get; set; }

    [JsonProperty("revit_version")]
    public string RevitVersion { get; set; } = "2026";
}

public class CodeGenerationResponse
{
    [JsonProperty("code")]
    public string Code { get; set; } = string.Empty;

    [JsonProperty("explanation")]
    public string Explanation { get; set; } = string.Empty;

    [JsonProperty("parameters_used")]
    public List<string> ParametersUsed { get; set; } = new();

    [JsonProperty("confidence")]
    public double Confidence { get; set; }

    [JsonProperty("warnings")]
    public List<string> Warnings { get; set; } = new();
}

public class DynamoGenerationRequest
{
    [JsonProperty("prompt")]
    public string Prompt { get; set; } = string.Empty;

    [JsonProperty("context")]
    public string? Context { get; set; }

    [JsonProperty("revit_version")]
    public string RevitVersion { get; set; } = "2026";
}

public class DynamoGenerationResponse
{
    [JsonProperty("script")]
    public string Script { get; set; } = string.Empty;

    [JsonProperty("node_suggestions")]
    public List<string> NodeSuggestions { get; set; } = new();

    [JsonProperty("explanation")]
    public string Explanation { get; set; } = string.Empty;

    [JsonProperty("confidence")]
    public double Confidence { get; set; }

    [JsonProperty("warnings")]
    public List<string> Warnings { get; set; } = new();
}
