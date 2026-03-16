using Autodesk.Revit.DB;
using Newtonsoft.Json;

namespace RevitFamilyEngine.Services;

/// <summary>
/// Extracts context from the active Revit FamilyDocument to include in AI prompts.
/// </summary>
public class RevitContextService
{
    private readonly Document _doc;

    public RevitContextService(Document doc)
    {
        _doc = doc;
    }

    public string GetFamilyContext()
    {
        var context = new Dictionary<string, object>();

        if (_doc is not FamilyDocument familyDoc)
        {
            context["error"] = "Not a family document";
            return JsonConvert.SerializeObject(context);
        }

        // Category
        context["category"] = familyDoc.OwnerFamily.FamilyCategory?.Name ?? "Unknown";
        context["family_name"] = familyDoc.Title;

        // Existing parameters
        var famMgr = familyDoc.FamilyManager;
        var parameters = new List<Dictionary<string, object>>();
        foreach (FamilyParameter fp in famMgr.Parameters)
        {
            parameters.Add(new Dictionary<string, object>
            {
                ["name"] = fp.Definition.Name,
                ["type"] = fp.Definition.ParameterType.ToString(),
                ["group"] = fp.Definition.ParameterGroup.ToString(),
                ["is_instance"] = fp.IsInstance,
                ["formula"] = fp.Formula ?? "",
            });
        }
        context["parameters"] = parameters;

        // Existing types
        var types = new List<string>();
        foreach (FamilyType ft in famMgr.Types)
            types.Add(ft.Name);
        context["types"] = types;

        // Geometry element types present
        var geomTypes = new HashSet<string>();
        var collector = new FilteredElementCollector(familyDoc)
            .WhereElementIsNotElementType();
        foreach (Element e in collector)
        {
            string typeName = e.GetType().Name;
            if (typeName is "Extrusion" or "Revolution" or "Blend" or "Sweep" or "SweptBlend")
                geomTypes.Add(typeName);
        }
        context["geometry_types"] = geomTypes.ToList();

        // Active view type
        context["active_view"] = familyDoc.ActiveView?.ViewType.ToString() ?? "None";

        return JsonConvert.SerializeObject(context, Formatting.Indented);
    }
}
