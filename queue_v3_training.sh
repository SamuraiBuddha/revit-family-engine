#!/usr/bin/env bash
# =============================================================================
# queue_v3_training.sh
#
# Second-iteration training: 10x oversample of gap pairs (2485 base + 120 gap
# repetitions = 2593 total, gap presence 0.48% -> 4.6%). Run this if v2
# probing scored below the 14/15 pass threshold but still showed improvement
# over :latest baseline.
#
# Usage:
#   ./queue_v3_training.sh          # dry-run: show what it would do, no changes
#   ./queue_v3_training.sh --go     # execute: swap dataset + kick off training
#
# Safety: refuses to run if a training process is already active in WSL.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
V3_JSON="${REPO_ROOT}/output/revit_training_data_v3.json"
WSL_DATA_PATH="/root/revit-training/data/revit_training_data.json"
WSL_PREPARED_PATH="/root/revit-training/data/prepared"
WSL_OUTPUT_DIR="/root/revit-training/output/revit-qwen3-coder-qlora"
WSL_TRAIN_LOG="/root/revit-training/train.log"
WSL_RUN_SCRIPT="/root/revit-training/run_train.sh"

GO=false
if [ "${1:-}" = "--go" ]; then GO=true; fi

# ---- preflight --------------------------------------------------------------

if [ ! -f "$V3_JSON" ]; then
    echo "[ERROR] $V3_JSON not found."
    echo "        Rebuild via the oversampling Python snippet or check the output/ dir."
    exit 2
fi

v3_size=$(wc -c < "$V3_JSON")
v3_pairs=$(python3 -c "import json; print(len(json.load(open(r'$V3_JSON'))))")

echo "=== v3 training plan ==="
echo "  Dataset:        $V3_JSON"
echo "  Size:           $(numfmt --to=iec "$v3_size") ($v3_pairs pairs)"
echo "  Target in WSL:  $WSL_DATA_PATH"
echo "  Will back up:   $WSL_OUTPUT_DIR -> ${WSL_OUTPUT_DIR}.v2-backup"
echo "  Will clear:     $WSL_PREPARED_PATH"
echo "  Then launch:    $WSL_RUN_SCRIPT (via nohup, background)"
echo ""

# Check for running training
running=$(wsl -d Ubuntu-22.04 bash -c "pgrep -f 'axolotl.cli.train' | head -1" 2>/dev/null || true)
if [ -n "$running" ]; then
    echo "[ERROR] A training process is already active in WSL (PID $running)."
    echo "        Wait for it to finish before queueing v3."
    echo "        Check progress:  wsl -d Ubuntu-22.04 bash -c \"tail -f $WSL_TRAIN_LOG\""
    exit 1
fi

# Check there's actually a v2 adapter to back up
has_v2=$(wsl -d Ubuntu-22.04 bash -c "[ -d '$WSL_OUTPUT_DIR' ] && echo yes || echo no" 2>/dev/null || echo "no")
if [ "$has_v2" = "no" ]; then
    echo "[WARN] No v2 adapter found at $WSL_OUTPUT_DIR -- are you sure v2 finished?"
    echo "       If this is intentional (e.g. skipping straight to v3), proceed with --go."
    if [ "$GO" = false ]; then echo ""; fi
fi

# ---- dry-run or execute -----------------------------------------------------

if [ "$GO" = false ]; then
    echo ""
    echo "Dry run. Re-run with --go to execute."
    echo ""
    echo "After launch, track progress:"
    echo "  wsl -d Ubuntu-22.04 bash -c \"tail -f $WSL_TRAIN_LOG\""
    echo ""
    echo "Estimated duration: ~90 min on A5000 (84 steps x ~65 s/step)."
    echo "Note: v3 has 2593 pairs vs v2's 2485; step count may rise by a few."
    exit 0
fi

echo "=== Executing v3 training launch ==="
echo ""

# 1. Copy dataset to WSL
echo "[1/4] Copying v3 dataset to WSL..."
wsl -d Ubuntu-22.04 bash -c "cp '/mnt/c/Users/JordanEhrig/Documents/GitHub/revit-family-engine/output/revit_training_data_v3.json' '$WSL_DATA_PATH'"
echo "      [OK] $(wsl -d Ubuntu-22.04 bash -c "wc -c < '$WSL_DATA_PATH'") bytes copied"

# 2. Back up v2 adapter
if [ "$has_v2" = "yes" ]; then
    echo "[2/4] Backing up v2 adapter..."
    wsl -d Ubuntu-22.04 bash -c "rm -rf '${WSL_OUTPUT_DIR}.v2-backup' && mv '$WSL_OUTPUT_DIR' '${WSL_OUTPUT_DIR}.v2-backup'"
    echo "      [OK] $WSL_OUTPUT_DIR -> ${WSL_OUTPUT_DIR}.v2-backup"
else
    echo "[2/4] No v2 adapter to back up, skipping"
fi

# 3. Clear prepared cache (critical: axolotl reuses tokenized data otherwise)
echo "[3/4] Clearing prepared cache..."
wsl -d Ubuntu-22.04 bash -c "rm -rf '$WSL_PREPARED_PATH' && echo '      [OK] cache cleared' || echo '      [OK] cache already clear'"

# 4. Kick off training in background
echo "[4/4] Launching training in background..."
wsl -d Ubuntu-22.04 bash -c "cd /root/revit-training && nohup bash run_train.sh > /root/revit-training/train.bgout 2>&1 & echo \$! > /root/revit-training/train.pid"

# Verify it actually started
sleep 2
new_pid=$(wsl -d Ubuntu-22.04 bash -c "pgrep -f 'axolotl.cli.train' | head -1" 2>/dev/null || true)
if [ -n "$new_pid" ]; then
    echo "      [OK] training launched (PID $new_pid)"
else
    echo "      [WARN] could not detect training process yet -- may still be loading"
fi

echo ""
echo "=== v3 training kicked off ==="
echo "  Monitor:   wsl -d Ubuntu-22.04 bash -c \"tail -f $WSL_TRAIN_LOG\""
echo "  ETA:       ~90 min"
echo "  When done, run:"
echo "    1. bash ./merge_and_register.sh   # merge + quant + register as :v2 (overwrites the v2 tag)"
echo "    2. bash ./promote_and_rollback.sh # probe + decide promote to :latest"
echo ""
echo "  If v3 also falls short of 14/15, inspect the gap diagnostic output"
echo "  and author a targeted v4 pair set before another training cycle."
