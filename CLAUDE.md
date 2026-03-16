# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**Revit Family Engine (RFE)** -- a fine-tuned LLM system for AI-powered Revit family creation in C#. Three-tier architecture:

1. **Revit C#/.NET Add-in** (`addin/`) -- IExternalApplication add-in with ribbon commands, communicates with backend via HTTP
2. **FastAPI Backend** (`backend/`, port 8001) -- routes prompts to Ollama, resolves parameter spaces
3. **Ollama Local LLM** -- fine-tuned Qwen2.5-Coder-32B via QLoRA/Axolotl

All inference runs locally. No cloud dependency.

Integrations:
- `../dynamo-node-search/` -- Dynamo specialist, used for the `dynamo` domain
- `building-code-mcp` MCP server -- building code compliance for the `building_code` domain
- `../auto-claw/` -- visual pipeline for spec-sheet-to-family automation

## CRITICAL: Revit Internal Units

**Revit internal units are FEET for length.** All mm values must be divided by 304.8.
Angles must be in radians (degrees * pi / 180).

```python
MM_TO_FT = 1.0 / 304.8
# 300mm = 300 / 304.8 = 0.984252 ft
```

**FamilyManager operations must occur OUTSIDE Transaction blocks.**
**Geometry creation (NewExtrusion, etc.) must occur INSIDE Transaction blocks.**

## Common Commands

### Backend
```bash
python -m venv venv
venv/Scripts/activate  # Windows
pip install -r requirements.txt
cd .. && uvicorn backend.main:app --reload --port 8001
```

### Training Pipeline
```bash
python training_pipeline/run_pipeline.py --output-dir output --format alpaca
```

### Fine-tuning & Deployment
```bash
axolotl train axolotl_revit_config.yml
python -m axolotl.cli.merge_lora axolotl_revit_config.yml
ollama create revit-family-32b --modelfile Modelfile
```

### Testing
```bash
pytest
pytest tests/test_parameter_space.py -v
black .
ruff check .
mypy .
```

### C# Add-in (Windows/Visual Studio)
```
# Open addin/RevitFamilyEngine.csproj in Visual Studio
# Build -> copy DLL to %AppData%\Autodesk\Revit\Addins\2026\
# Copy addin/RevitFamilyEngine.addin to same folder
```

## Architecture

### Domains (7 total, used in backend system prompts and API requests)
- `family_geometry` -- NewExtrusion, NewRevolution, NewBlend, NewSweep
- `family_parameters` -- FamilyManager, FamilyParameter, FamilyType, formulas
- `constraints` -- ReferencePlane, NewLinearDimension, FamilyLabel, EqualConstraint
- `family_types` -- type catalog CSV, nested family loading, type iteration
- `gdt` -- DimensionType tolerance, ASME Y14.5-2018 via Revit annotation
- `dynamo` -- Python Dynamo node scripts (ProtoGeometry, RevitNodes)
- `building_code` -- IBC/NFPA compliance validation (bridges to building-code-mcp)

### Core Abstraction: Parameterization-First

`parameterization/parameter_space.py` defines ParameterSpace objects; each generates
hundreds of C# training pairs via Cartesian product.

Predefined spaces: `wall_family`, `door_family`, `column_family`, `window_family`, `extrusion_solid`

### Key Config Files
- `axolotl_revit_config.yml` -- Qwen2.5-Coder-32B, lora_r=32, lr=1e-4, seq_len=4096
- `Modelfile` -- Ollama model definition with Revit-specific system prompt

## Extending

**New parameter space**: define in `parameter_space.py` --> add resolver template in `parameter_resolver.py`
**New generator**: add to `training_pipeline/generators/` --> register in `run_pipeline.py`
**New domain**: add system prompt to `backend/ollama_backend.py` --> add to `VALID_DOMAINS` in `backend/models.py`
