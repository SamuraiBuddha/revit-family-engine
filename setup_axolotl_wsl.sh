#!/usr/bin/env bash
# setup_axolotl_wsl.sh
# Run inside WSL2 Ubuntu-22.04: bash setup_axolotl_wsl.sh
set -e

echo "[1/7] Installing system dependencies..."
apt-get update -q
apt-get install -y -q wget git build-essential ninja-build libssl-dev \
    python3-dev pkg-config

echo "[2/7] Installing Miniconda..."
if [ ! -d "$HOME/miniconda3" ]; then
    wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
        -O /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -p "$HOME/miniconda3"
    rm /tmp/miniconda.sh
fi
export PATH="$HOME/miniconda3/bin:$PATH"
conda init bash
source "$HOME/miniconda3/etc/profile.d/conda.sh"

echo "[3/7] Creating axolotl conda environment (Python 3.11)..."
conda create -y -n axolotl python=3.11
conda activate axolotl

echo "[4/7] Installing CUDA toolkit 12.1 (compiler + libraries for flash-attn)..."
conda install -y -c nvidia/label/cuda-12.1.0 cuda-toolkit

echo "[5/7] Installing PyTorch 2.4 + CUDA 12.1..."
pip install --quiet torch==2.4.1 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

echo "  Verifying GPU visibility..."
python -c "
import torch
assert torch.cuda.is_available(), 'CUDA not available!'
name = torch.cuda.get_device_name(0)
vram = torch.cuda.get_device_properties(0).total_memory / 1e9
print(f'  [OK] {name} | {vram:.1f} GB VRAM')
"

echo "[6/7] Installing Axolotl + flash-attn..."
pip install --quiet packaging
pip install --quiet 'axolotl[flash-attn,deepspeed] @ git+https://github.com/axolotl-ai-cloud/axolotl.git'

echo "[7/7] Copying training data to WSL2 home..."
mkdir -p "$HOME/revit-training/data"
cp /mnt/c/Users/JordanEhrig/Documents/GitHub/revit-family-engine/output/revit_training_data.json \
    "$HOME/revit-training/data/revit_training_data.json"

SAMPLE_COUNT=$(python -c "import json; d=json.load(open('$HOME/revit-training/data/revit_training_data.json')); print(len(d))")
echo "  [OK] $SAMPLE_COUNT training samples copied"

echo ""
echo "================================================================"
echo "  Setup complete. To train:"
echo ""
echo "  conda activate axolotl"
echo "  cd ~/revit-training"
echo "  axolotl train revit_qlora.yml"
echo "================================================================"
