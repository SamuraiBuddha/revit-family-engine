# Revit Family Engine

AI-powered Revit family creation system using a locally fine-tuned LLM. Generates
compilable C# Revit API code from natural language descriptions of parametric family
geometry, parameters, constraints, GD&T annotations, and Dynamo scripts.

## Architecture

Three-tier system, all running locally:

1. **Revit Add-in** (`addin/`) -- C#/.NET 8.0 add-in with ribbon commands
2. **FastAPI Backend** (`backend/`, port 8001) -- LLM routing and parameter resolution
3. **Ollama LLM** -- Fine-tuned Qwen2.5-Coder-32B via QLoRA

Integrates with the `dynamo-node-search` Dynamo specialist and `building-code-mcp`
compliance server in the same ecosystem.

## Seven Domains

| Domain | Coverage |
|---|---|
| `family_geometry` | Extrusion, Revolution, Blend, Sweep, void forms |
| `family_parameters` | FamilyManager, FamilyParameter, formulas, type catalogs |
| `constraints` | ReferencePlane, dimensions, FamilyLabel, EqualConstraint |
| `family_types` | Type iteration, nested family loading, CSV type catalogs |
| `gdt` | ASME Y14.5-2018 tolerances via Revit DimensionType |
| `dynamo` | Python Dynamo node scripts (ProtoGeometry / RevitNodes) |
| `building_code` | IBC/NFPA compliance validation |

## Quick Start

```bash
# Backend
python -m venv venv && venv/Scripts/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8001

# Generate training data
python training_pipeline/run_pipeline.py --output-dir output

# Fine-tune (requires GPU with ~24GB VRAM for 32B model)
axolotl train axolotl_revit_config.yml

# Deploy to Ollama
ollama create revit-family-32b --modelfile Modelfile
```

## Critical Notes

- Revit internal units: **feet** for length (mm / 304.8), **radians** for angles
- `FamilyManager` operations must occur **outside** `Transaction` blocks
- Geometry creation (`NewExtrusion`, etc.) must occur **inside** `Transaction` blocks
- Add-in runs on port 8001 (not 8000, to avoid conflict with sw-semantic-engine)

## Training Data

The parameterization framework generates training data via Cartesian product:
five predefined parameter spaces produce hundreds of C# code examples automatically.
Three specialized generators (geometry, parameters, GD&T) contribute ~750 additional pairs.

## Related Projects

- `sw-semantic-engine` -- same architecture for SolidWorks COM API
- `dynamo-node-search` -- Dynamo specialist LLM
- `auto-claw` -- automated family creation from manufacturer spec sheets
- `building-code-mcp` -- building code compliance MCP server
