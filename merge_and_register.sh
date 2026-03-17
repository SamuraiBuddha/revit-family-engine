#!/usr/bin/env bash
# merge_and_register.sh
# Run after axolotl training completes (inside WSL2 with axolotl env active):
#
#   conda activate axolotl
#   bash /root/revit-training/merge_and_register.sh
#
# What this does:
#   1. Merges LoRA adapter back into base weights (full bf16 model)
#   2. Converts to GGUF Q4_K_M with llama.cpp
#   3. Registers with local Ollama as "revit-coder:30b"

set -e

ADAPTER_DIR="/root/revit-training/output/revit-qwen3-coder-qlora"
MERGED_DIR="/root/revit-training/output/merged-bf16"
GGUF_DIR="/root/revit-training/output/gguf"
MODEL_NAME="revit-coder:30b"
MODELFILE_SRC="/mnt/c/Users/JordanEhrig/Documents/GitHub/revit-family-engine/Modelfile"

export PATH=/root/miniconda3/envs/axolotl/bin:/root/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export CUDA_HOME=/root/miniconda3/envs/axolotl

echo "================================================================"
echo "  Step 1: Merge LoRA adapter into base model (bf16)"
echo "================================================================"

# Find the latest checkpoint
LATEST_CKPT=$(ls -d "$ADAPTER_DIR/checkpoint-"* 2>/dev/null | sort -V | tail -1)
if [ -z "$LATEST_CKPT" ]; then
    echo "[WARN] No checkpoint subfolder found; using $ADAPTER_DIR directly"
    LATEST_CKPT="$ADAPTER_DIR"
fi
echo "  Using adapter: $LATEST_CKPT"

axolotl merge-lora axolotl_revit_config.yml \
    --lora-model-dir "$LATEST_CKPT" \
    --output-dir "$MERGED_DIR" 2>&1 | tail -10

echo "[OK] Merged model saved to $MERGED_DIR"

echo ""
echo "================================================================"
echo "  Step 2: Convert to GGUF Q4_K_M with llama.cpp"
echo "================================================================"

LLAMACPP_DIR="/root/llama.cpp"
if [ ! -d "$LLAMACPP_DIR" ]; then
    echo "  Cloning llama.cpp..."
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "$LLAMACPP_DIR"
    cd "$LLAMACPP_DIR"
    pip install --quiet gguf sentencepiece
fi

cd "$LLAMACPP_DIR"
mkdir -p "$GGUF_DIR"

echo "  Converting to f16 GGUF first..."
python convert_hf_to_gguf.py \
    "$MERGED_DIR" \
    --outfile "$GGUF_DIR/revit-coder-30b-f16.gguf" \
    --outtype f16

echo "  Quantizing to Q4_K_M..."
./llama-quantize \
    "$GGUF_DIR/revit-coder-30b-f16.gguf" \
    "$GGUF_DIR/revit-coder-30b-Q4_K_M.gguf" \
    Q4_K_M

echo "[OK] GGUF saved to $GGUF_DIR/revit-coder-30b-Q4_K_M.gguf"

echo ""
echo "================================================================"
echo "  Step 3: Register with Ollama"
echo "================================================================"

# Write local Modelfile pointing at the GGUF
MODELFILE_LOCAL="$GGUF_DIR/Modelfile"
cat > "$MODELFILE_LOCAL" << 'MODELFILEEOF'
FROM /root/revit-training/output/gguf/revit-coder-30b-Q4_K_M.gguf

SYSTEM """You are an expert Revit family creation AI. Generate precise, compilable C# code using the Revit API for parametric family geometry, parameters, constraints, and type management.

Rules:
- Use Revit internal units: feet for length (mm / 304.8), radians for angles
- Always wrap geometry creation in Transaction blocks
- FamilyManager operations happen OUTSIDE Transaction blocks
- Reference planes must exist before dimensions that reference them
- Parameters must be assigned to types via famMgr.Set()
- Use proper enum types (BuiltInParameterGroup, ParameterType)
- Code must compile against Revit 2024+ API (.NET 8.0)
- Namespace: Autodesk.Revit.DB, Autodesk.Revit.UI
"""

PARAMETER stop "<|im_end|>"
PARAMETER stop "Human:"
PARAMETER stop "User:"
PARAMETER temperature 0.15
PARAMETER top_p 0.9
MODELFILEEOF

# Run ollama from Windows side via PowerShell (Ollama runs on Windows, not WSL2)
echo "  Registering $MODEL_NAME with Ollama on Windows host..."
powershell.exe -Command "ollama create revit-coder:30b -f '$MODELFILE_LOCAL'"

echo ""
echo "[OK] Done. Test with:"
echo "     ollama run revit-coder:30b"
echo ""
echo "  Adapter:       $LATEST_CKPT"
echo "  Merged bf16:   $MERGED_DIR"
echo "  GGUF Q4_K_M:   $GGUF_DIR/revit-coder-30b-Q4_K_M.gguf"
echo "  Ollama model:  $MODEL_NAME"
