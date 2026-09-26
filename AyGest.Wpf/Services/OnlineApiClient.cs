using System.Net.Http;
using System.Net.Http.Json;
namespace AyGest.Wpf.Services;
public sealed class OnlineApiClient : IDisposable
{
 private readonly HttpClient _http; public string? TenantId{get;private set;} public string? LicenseKey{get;private set;} public bool IsOnline{get;private set;}
 public OnlineApiClient(string baseUrl){if(!Uri.TryCreate(baseUrl,UriKind.Absolute,out var uri))throw new ArgumentException("URL do servidor inválida.",nameof(baseUrl));_http=new HttpClient{BaseAddress=new Uri(uri.ToString().TrimEnd('/')+"/"),Timeout=TimeSpan.FromSeconds(15)};}
 public async Task<bool> CheckHealthAsync(CancellationToken ct=default){try{using var r=await _http.GetAsync("health",ct);IsOnline=r.IsSuccessStatusCode;return IsOnline;}catch{IsOnline=false;return false;}}
 public async Task<LicenseResponse> ActivateAsync(string key,string deviceId,string? tenantId=null,CancellationToken ct=default){try{var r=await _http.PostAsJsonAsync("api/v1/licenses/activate",new{key,device_id=deviceId,tenant_id=tenantId},ct);var d=await r.Content.ReadFromJsonAsync<LicenseResponse>(cancellationToken:ct)??new();IsOnline=r.IsSuccessStatusCode;if(d.Active){LicenseKey=key;TenantId=d.TenantId;}return d;}catch{IsOnline=false;return new LicenseResponse{Message="Servidor indisponível."};}}
 public async Task<LicenseResponse> VerifyAsync(string key,string deviceId,string? tenantId=null,CancellationToken ct=default){try{var r=await _http.PostAsJsonAsync("api/v1/licenses/verify",new{key,device_id=deviceId,tenant_id=tenantId},ct);var d=await r.Content.ReadFromJsonAsync<LicenseResponse>(cancellationToken:ct)??new();IsOnline=r.IsSuccessStatusCode;if(d.Active){LicenseKey=key;TenantId=d.TenantId;}return d;}catch{IsOnline=false;return new LicenseResponse{Message="Servidor indisponível."};}}
 public async Task<bool> PushEventAsync(string eventType,object payload,string deviceId,CancellationToken ct=default){if(string.IsNullOrWhiteSpace(TenantId)||string.IsNullOrWhiteSpace(LicenseKey))return false;try{var id=Guid.NewGuid().ToString("N");var r=await _http.PostAsJsonAsync("api/v1/sync/events",new{tenant_id=TenantId,event_id=id,event_type=eventType,payload,license_key=LicenseKey,device_id=deviceId},ct);return r.IsSuccessStatusCode;}catch{return false;}}
 public async Task<SyncEventsResponse?> PullEventsAsync(long afterId,string deviceId,CancellationToken ct=default){if(string.IsNullOrWhiteSpace(TenantId)||string.IsNullOrWhiteSpace(LicenseKey))return null;try{return await _http.GetFromJsonAsync<SyncEventsResponse>($"api/v1/sync/events?tenantId={Uri.EscapeDataString(TenantId)}&afterId={afterId}&limit=500&licenseKey={Uri.EscapeDataString(LicenseKey)}&deviceId={Uri.EscapeDataString(deviceId)}",ct);}catch{return null;}}
 public void Dispose()=>_http.Dispose();
}
public sealed class LicenseResponse{public bool Active{get;set;}public string? Key{get;set;}public string? TenantId{get;set;}public string? Plan{get;set;}public string? ExpiresAt{get;set;}public string? Message{get;set;}}
public sealed class SyncEventsResponse{public string? TenantId{get;set;}public List<SyncEventDto> Events{get;set;}=[];}
public sealed class SyncEventDto{public long Id{get;set;}public string? EventId{get;set;}public string? EventType{get;set;}public string? Payload{get;set;}public string? CreatedAt{get;set;}}
