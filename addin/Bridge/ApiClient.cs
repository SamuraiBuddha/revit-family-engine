using System.Net.Http;
using System.Text;
using Newtonsoft.Json;
using RevitFamilyEngine.Models;

namespace RevitFamilyEngine;

/// <summary>
/// HTTP bridge to the Python FastAPI backend (port 8001).
/// </summary>
public class ApiClient : IDisposable
{
    private readonly HttpClient _http;
    private readonly string _baseUrl;
    private bool _disposed;

    public ApiClient(string baseUrl = "http://127.0.0.1:8001")
    {
        _baseUrl = baseUrl.TrimEnd('/');
        _http = new HttpClient { Timeout = TimeSpan.FromSeconds(120) };
    }

    public async Task<CodeGenerationResponse> GenerateCodeAsync(CodeGenerationRequest request)
    {
        string json = JsonConvert.SerializeObject(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        HttpResponseMessage response = await _http.PostAsync($"{_baseUrl}/api/generate-code", content);
        response.EnsureSuccessStatusCode();
        string body = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<CodeGenerationResponse>(body)
            ?? throw new InvalidOperationException("Null response from backend");
    }

    public async Task<DynamoGenerationResponse> GenerateDynamoScriptAsync(DynamoGenerationRequest request)
    {
        string json = JsonConvert.SerializeObject(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        HttpResponseMessage response = await _http.PostAsync($"{_baseUrl}/api/generate-dynamo", content);
        response.EnsureSuccessStatusCode();
        string body = await response.Content.ReadAsStringAsync();
        return JsonConvert.DeserializeObject<DynamoGenerationResponse>(body)
            ?? throw new InvalidOperationException("Null response from backend");
    }

    public async Task<bool> IsHealthyAsync()
    {
        try
        {
            HttpResponseMessage r = await _http.GetAsync($"{_baseUrl}/health");
            return r.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    public void Dispose()
    {
        if (!_disposed) { _http.Dispose(); _disposed = true; }
        GC.SuppressFinalize(this);
    }
}
