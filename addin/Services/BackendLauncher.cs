using System.Diagnostics;
using System.IO;

namespace RevitFamilyEngine.Services;

/// <summary>
/// Auto-starts the Python FastAPI backend and monitors its health.
/// Looks for .rfe-port file to discover the actual listening port.
/// </summary>
public class BackendLauncher : IDisposable
{
    private const string PortFile = ".rfe-port";
    private const int BackendPort = 8001;
    private const int StartupTimeoutMs = 30_000;

    private Process? _backendProcess;
    private bool _disposed;

    public int ActualPort { get; private set; } = BackendPort;

    public async Task EnsureServicesRunningAsync()
    {
        if (await IsBackendRunningAsync()) return;

        string pythonExe = FindPython();
        string projectRoot = FindProjectRoot();

        var psi = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = $"-m uvicorn backend.main:app --port {BackendPort} --host 127.0.0.1",
            WorkingDirectory = projectRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
        };

        _backendProcess = Process.Start(psi);

        // Wait for backend to come up
        int elapsed = 0;
        while (elapsed < StartupTimeoutMs)
        {
            await Task.Delay(500);
            elapsed += 500;
            if (await IsBackendRunningAsync()) break;
        }

        // Try to read port from file
        string portFilePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), PortFile);
        if (File.Exists(portFilePath) &&
            int.TryParse(File.ReadAllText(portFilePath).Trim(), out int port))
        {
            ActualPort = port;
        }
    }

    private static async Task<bool> IsBackendRunningAsync()
    {
        try
        {
            using var http = new System.Net.Http.HttpClient
            {
                Timeout = TimeSpan.FromSeconds(2)
            };
            var r = await http.GetAsync($"http://127.0.0.1:{BackendPort}/health");
            return r.IsSuccessStatusCode;
        }
        catch { return false; }
    }

    private static string FindPython()
    {
        // Check common locations; prefer venv
        var candidates = new[]
        {
            Path.Combine(FindProjectRoot(), "venv", "Scripts", "python.exe"),
            Path.Combine(FindProjectRoot(), ".venv", "Scripts", "python.exe"),
            "python",
            "python3",
        };
        foreach (var p in candidates)
            if (File.Exists(p) || !p.Contains(Path.DirectorySeparatorChar)) return p;
        return "python";
    }

    private static string FindProjectRoot()
    {
        // Walk up from the assembly location to find the project root
        string? dir = Path.GetDirectoryName(typeof(BackendLauncher).Assembly.Location);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir, "requirements.txt")) &&
                Directory.Exists(Path.Combine(dir, "backend")))
                return dir;
            dir = Path.GetDirectoryName(dir);
        }
        return Environment.CurrentDirectory;
    }

    public void Dispose()
    {
        if (_disposed) return;
        try { _backendProcess?.Kill(entireProcessTree: true); } catch { }
        _backendProcess?.Dispose();
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}
