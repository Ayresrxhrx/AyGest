using System.Net.Http;
using System.Net.Http.Json;
namespace AyGest.Wpf.Services;
public sealed class OnlineApiClient : IDisposable
{
    private readonly HttpClient _http;
    public string? TenantId { get; private set; }
    public string? LicenseKey { get; private set; }
    public bool IsOnline { get; private set; }
    public OnlineApiClient(string baseUrl)
    {
        if (!Uri.TryCreate(baseUrl, UriKind.Absolute, out var uri)) throw new ArgumentException("URL do servidor inválida.", nameof(baseUrl));
        _http = new HttpClient { BaseAddress = new Uri(uri.ToString().TrimEnd('/') + "/"), Timeout = TimeSpan.FromSeconds(15) };
    }
    public async Task<bool> CheckHealthAsync(CancellationToken ct=default)
    {
        try { using var r=await _http.GetAsync("health",ct); IsOnline=r.IsSuccessStatusCode; return IsOnline; }
        catch { IsOnline=false; return false; }
    }
    public async Task<LicenseResponse> ActivateAsync(string key,string deviceId,string? tenantId=null,CancellationToken ct=default)
    {
        try
        {
            var response=await _http.PostAsJsonAsync("api/v1/licenses/activate",new { key, device_id=deviceId, tenant_id=tenantId },ct);
            var data=await response.Content.ReadFromJsonAsync<LicenseResponse>(cancellationToken:ct) ?? new();
            IsOnline=response.IsSuccessStatusCode;
            if(data.Active){LicenseKey=key;TenantId=data.TenantId;}
            return data;
        }
        catch { IsOnline=false; return new LicenseResponse{Active=false,Message="Servidor indisponível."}; }
    }
    public async Task<LicenseResponse> VerifyAsync(string key,string deviceId,string? tenantId=null,CancellationToken ct=default)
    {
        try { var response=await _http.PostAsJsonAsync("api/v1/licenses/verify",new { key, device_id=deviceId, tenant_id=tenantId },ct); var data=await response.Content.ReadFromJsonAsync<LicenseResponse>(cancellationToken:ct) ?? new(); IsOnline=response.IsSuccessStatusCode; if(data.Active) TenantId=data.TenantId; return data; }
        catch { IsOnline=false; return new LicenseResponse{Active=false,Message="Servidor indisponível."}; }
    }
    public async Task<bool> PushEventAsync(object payload,CancellationToken ct=default)
    {
        if(string.IsNullOrWhiteSpace(TenantId)) return false;
        try { var response=await _http.PostAsJsonAsync("api/v1/sync/events",new { tenant_id=TenantId,payload,utc=DateTime.UtcNow },ct); return response.IsSuccessStatusCode; } catch{return false;}
    }
    public void Dispose()=>_http.Dispose();
}
public sealed class LicenseResponse { public bool Active {get;set;} public string? Key {get;set;} public string? TenantId {get;set;} public string? Plan {get;set;} public string? ExpiresAt {get;set;} public string? Message {get;set;} }
