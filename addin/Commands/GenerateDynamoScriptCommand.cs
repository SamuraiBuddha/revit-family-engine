using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using RevitFamilyEngine.Models;

namespace RevitFamilyEngine.Commands;

[Transaction(TransactionMode.Manual)]
[Regeneration(RegenerationOption.Manual)]
public class GenerateDynamoScriptCommand : IExternalCommand
{
    public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
    {
        UIApplication uiApp = commandData.Application;

        TaskDialog promptDialog = new TaskDialog("Generate Dynamo Script")
        {
            MainContent = "Describe the Dynamo automation you want (e.g., 'Drive Width and Height from external spreadsheet'):",
            CommonButtons = TaskDialogCommonButtons.Ok | TaskDialogCommonButtons.Cancel,
        };

        if (promptDialog.Show() == TaskDialogResult.Cancel) return Result.Cancelled;

        string prompt = "Drive family Width, Height, and Depth from Dynamo input nodes";

        ApiClient? client = Application.ApiClient;
        if (client == null)
        {
            TaskDialog.Show("Error", "Backend client not initialized.");
            return Result.Failed;
        }

        try
        {
            var request = new DynamoGenerationRequest
            {
                Prompt = prompt,
                RevitVersion = uiApp.Application.VersionNumber,
            };

            var response = Task.Run(async () => await client.GenerateDynamoScriptAsync(request)).Result;

            string suggestions = response.NodeSuggestions.Count > 0
                ? "\n\nSuggested nodes:\n- " + string.Join("\n- ", response.NodeSuggestions)
                : "";

            TaskDialog result = new TaskDialog("Dynamo Script Generated")
            {
                MainContent = $"Confidence: {response.Confidence * 100:F0}%{suggestions}",
                ExpandedContent = response.Script,
                CommonButtons = TaskDialogCommonButtons.Close,
            };
            result.Show();
            return Result.Succeeded;
        }
        catch (Exception ex)
        {
            TaskDialog.Show("Dynamo Generation Error", ex.Message);
            return Result.Failed;
        }
    }
}
