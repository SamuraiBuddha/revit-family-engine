using Autodesk.Revit.UI;
using RevitFamilyEngine.Services;

namespace RevitFamilyEngine;

/// <summary>
/// Revit add-in entry point. Registers ribbon panel and auto-starts the Python backend.
/// </summary>
public class Application : IExternalApplication
{
    public static ApiClient? ApiClient { get; private set; }
    public static BackendLauncher? Launcher { get; private set; }

    private const string BackendUrl = "http://127.0.0.1:8001";
    private const string PanelName = "Revit Family Engine";

    public Result OnStartup(UIControlledApplication app)
    {
        try
        {
            ApiClient = new ApiClient(BackendUrl);
            Launcher = new BackendLauncher();
            _ = Task.Run(async () => await Launcher.EnsureServicesRunningAsync());
            RegisterRibbonPanel(app);
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            TaskDialog.Show("Revit Family Engine", $"Startup error: {ex.Message}");
            return Result.Failed;
        }
    }

    public Result OnShutdown(UIControlledApplication app)
    {
        Launcher?.Dispose();
        return Result.Succeeded;
    }

    private static void RegisterRibbonPanel(UIControlledApplication app)
    {
        RibbonPanel panel = app.CreateRibbonPanel(PanelName);

        // Generate Family Code button
        PushButtonData generateBtn = new PushButtonData(
            "GenerateFamilyCode",
            "Generate\nCode",
            typeof(Application).Assembly.Location,
            "RevitFamilyEngine.Commands.GenerateFamilyCodeCommand"
        );
        generateBtn.ToolTip = "Generate Revit family C# code with AI assistance";
        panel.AddItem(generateBtn);

        // Generate Dynamo Script button
        PushButtonData dynamoBtn = new PushButtonData(
            "GenerateDynamoScript",
            "Dynamo\nScript",
            typeof(Application).Assembly.Location,
            "RevitFamilyEngine.Commands.GenerateDynamoScriptCommand"
        );
        dynamoBtn.ToolTip = "Generate a Dynamo script for parametric family automation";
        panel.AddItem(dynamoBtn);
    }
}
