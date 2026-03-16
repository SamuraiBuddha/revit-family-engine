using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitFamilyEngine.Models;
using RevitFamilyEngine.Services;

namespace RevitFamilyEngine.Commands;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public class GenerateFamilyCodeCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        UIApplication uiApp = commandData.Application;
        Document doc = uiApp.ActiveUIDocument.Document;

        // Get prompt from user
        string? prompt = ShowPromptDialog("Generate Revit Family Code",
            "Describe the Revit family geometry or parameter you want to create:");
        if (string.IsNullOrWhiteSpace(prompt)) return Result.Cancelled;

        // Get domain from user
        string domain = ShowDomainPicker();

        // Extract Revit context
        string context = string.Empty;
        try
        {
            var contextService = new RevitContextService(doc);
            context = contextService.GetFamilyContext();
        }
        catch { /* context is optional */ }

        // Call backend
        ApiClient? client = Application.ApiClient;
        if (client == null)
        {
            TaskDialog.Show("Error", "Backend client not initialized.");
            return Result.Failed;
        }

        try
        {
            var request = new CodeGenerationRequest
            {
                Prompt = prompt,
                Domain = domain,
                Context = context,
                IncludeComments = true,
                RevitVersion = uiApp.Application.VersionNumber,
            };

            var response = Task.Run(async () => await client.GenerateCodeAsync(request)).Result;
            ShowResultDialog(response);
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            TaskDialog.Show("Generation Error", ex.Message);
            return Result.Failed;
        }
    }

    private static string? ShowPromptDialog(string title, string label)
    {
        // Simple TaskDialog with input -- production would use WPF dialog
        TaskDialog td = new TaskDialog(title)
        {
            MainContent = label,
            CommonButtons = TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel,
        };
        // Note: real input would require a WPF window; this is a placeholder
        return "Create a parametric extrusion driven by Width and Height parameters";
    }

    private static string ShowDomainPicker()
    {
        // Returns the domain string; production would use a ComboBox
        return "family_geometry";
    }

    private static void ShowResultDialog(CodeGenerationResponse response)
    {
        string confidence = $"{response.Confidence * 100:F0}%";
        string warnings = response.Warnings.Count > 0
            ? "\n\n[WARN] " + string.Join("\n[WARN] ", response.Warnings)
            : "";

        TaskDialog td = new TaskDialog("Generated Code")
        {
            MainContent = $"Confidence: {confidence}{warnings}\n\n{response.Explanation}",
            ExpandedContent = response.Code,
            CommonButtons = TaskDialogCommonButtons.Close,
        };
        td.Show();
    }
}
