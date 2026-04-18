#!/usr/bin/env bash
# =============================================================================
# promote_and_rollback.sh
#
# Probe the v2 model against the same gap-closure criteria that motivated its
# training. If it passes, promote v2 -> :latest (with the prior :latest
# preserved as :v1-backup for recovery). If it fails, print the failures and
# refuse to promote.
#
# Usage:
#   ./promote_and_rollback.sh              # probe + auto-decide
#   ./promote_and_rollback.sh --probe      # probe only, print verdict, exit
#   ./promote_and_rollback.sh --promote    # force promote (skips probe)
#   ./promote_and_rollback.sh --rollback   # restore :latest from :v1-backup
#
# Runs from either Git Bash or WSL -- Ollama HTTP is hit directly.
# =============================================================================

set -euo pipefail

# ---- config -----------------------------------------------------------------

CANDIDATE_TAG="revit-family-engine:v2"
PRODUCTION_TAG="revit-family-engine:latest"
BACKUP_TAG="revit-family-engine:v1-backup"
OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11434}"
PASS_THRESHOLD=11   # out of 15 total

# ---- helpers ----------------------------------------------------------------

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

ollama_list_has() {
    # Returns 0 if a tag is present, 1 otherwise
    curl -s "$OLLAMA_HOST/api/tags" \
        | python3 -c "import json, sys; d=json.load(sys.stdin); names=[m['name'] for m in d.get('models',[])]; sys.exit(0 if '$1' in names else 1)"
}

ollama_copy() {
    # Ollama has /api/copy; POST {source, destination}
    curl -sf -X POST "$OLLAMA_HOST/api/copy" \
        -H 'Content-Type: application/json' \
        -d "{\"source\":\"$1\",\"destination\":\"$2\"}" >/dev/null
}

probe_model() {
    # Args: model_tag, prompt_file, out_file
    local model="$1"
    local prompt_file="$2"
    local out_file="$3"

    # Build request JSON safely via python
    python3 -c "
import json, sys
prompt = open('$prompt_file').read()
req = {
    'model': '$model',
    'stream': False,
    'options': {'temperature': 0, 'num_ctx': 4096},
    'messages': [
        {'role': 'system', 'content': 'You are the Revit API specialist. Output compilable C# with transactions. No narration.'},
        {'role': 'user', 'content': prompt},
    ],
}
print(json.dumps(req))
" > "$tmp_dir/req.json"

    curl -sf -X POST --max-time 180 "$OLLAMA_HOST/api/chat" \
        -H 'Content-Type: application/json' \
        --data @"$tmp_dir/req.json" \
        | python3 -c "import json,sys; d=json.load(sys.stdin); sys.stdout.write(d.get('message',{}).get('content',''))" \
        > "$out_file"
}

# ---- probe scoring ----------------------------------------------------------

# Each probe returns its subtotal via stdout. Final line is "SCORE=<n>/<total>".

probe_1_parametric_extrusion() {
    local output_file="$1"
    local score=0
    local total=5

    echo "=== Probe 1: Parametric extrusion (5 criteria) ==="

    if ! grep -q "Alignment\.Create" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] No fabricated Alignment.Create"
    else
        echo "  [FAIL] Contains fabricated Alignment.Create"
    fi

    if ! grep -q "IsReferencesValidForLabel" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] No fabricated IsReferencesValidForLabel"
    else
        echo "  [FAIL] Contains fabricated IsReferencesValidForLabel"
    fi

    if grep -qE "FamilyCreate\s*\.\s*NewAlignment" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Uses FamilyCreate.NewAlignment"
    else
        echo "  [FAIL] Missing FamilyCreate.NewAlignment"
    fi

    if grep -qE "new\s+Transaction\s*\(" "$output_file" && grep -qE "tx\.Start|\.Start\s*\(" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Transaction wrapper present"
    else
        echo "  [FAIL] Missing Transaction wrapper"
    fi

    if grep -qE "\.FamilyLabel\s*=" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] FamilyLabel binding present"
    else
        echo "  [FAIL] Missing FamilyLabel binding"
    fi

    echo "SCORE=$score/$total"
}

probe_2_compute_references() {
    local output_file="$1"
    local score=0
    local total=5

    echo "=== Probe 2: Face reference extraction (5 criteria) ==="

    if grep -qE "ComputeReferences\s*=\s*true" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Sets Options.ComputeReferences = true"
    else
        echo "  [FAIL] Missing ComputeReferences = true"
    fi

    if grep -q "new Options" "$output_file" || grep -q "Options(" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Creates Options instance"
    else
        echo "  [FAIL] Missing Options instantiation"
    fi

    if grep -qE "get_Geometry|\.Geometry\[|GetGeometry" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Accesses geometry"
    else
        echo "  [FAIL] Missing geometry access"
    fi

    if grep -qE "PlanarFace|as\s+PlanarFace|is\s+PlanarFace" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Casts to PlanarFace"
    else
        echo "  [FAIL] Missing PlanarFace cast"
    fi

    if grep -qE "\.Reference\b|\.GetReference\(" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Extracts Reference from face"
    else
        echo "  [FAIL] Missing Reference extraction"
    fi

    echo "SCORE=$score/$total"
}

probe_3_family_label_validity() {
    local output_file="$1"
    local score=0
    local total=5

    echo "=== Probe 3: FamilyLabel validity rules (5 criteria) ==="

    if ! grep -q "IsReferencesValidForLabel" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Does not invent IsReferencesValidForLabel"
    else
        echo "  [FAIL] Invents IsReferencesValidForLabel"
    fi

    if grep -qiE "InvalidOperationException|throws?\s+InvalidOperation" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Mentions InvalidOperationException"
    else
        echo "  [FAIL] Missing InvalidOperationException reference"
    fi

    if grep -qiE "try\b|catch\b" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Recommends try/catch validation"
    else
        echo "  [FAIL] Missing try/catch pattern"
    fi

    if grep -qiE "references\.|reference\s+count|at\s+least\s+2|fewer\s+than\s+2" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Mentions reference-count rule"
    else
        echo "  [FAIL] Missing reference-count rule"
    fi

    if grep -qiE "EQ|equality|equal\s+constra" "$output_file"; then
        score=$((score + 1)); echo "  [PASS] Mentions EQ-constraint limitation"
    else
        echo "  [FAIL] Missing EQ-constraint rule"
    fi

    echo "SCORE=$score/$total"
}

# ---- actions ----------------------------------------------------------------

run_probes() {
    if ! ollama_list_has "$CANDIDATE_TAG"; then
        echo "[ERROR] Candidate model not found: $CANDIDATE_TAG"
        echo "        Did merge_and_register.sh finish? Check 'ollama list'."
        exit 2
    fi

    echo "=== Probing $CANDIDATE_TAG ==="
    echo ""

    # Probe 1
    cat > "$tmp_dir/p1.txt" <<'EOF'
Write Revit C# that creates a parametric Width extrusion inside a family document.
The extrusion's left and right faces must be aligned AND locked to the Left and
Right reference planes, with a labeled dimension so changing Width actually flexes
the extrusion. Use the canonical Revit family API. Include transaction management.
EOF
    probe_model "$CANDIDATE_TAG" "$tmp_dir/p1.txt" "$tmp_dir/p1_out.txt"
    p1_out=$(probe_1_parametric_extrusion "$tmp_dir/p1_out.txt")
    echo "$p1_out"
    p1_score=$(echo "$p1_out" | grep -oE "SCORE=[0-9]+" | tail -1 | cut -d= -f2)
    echo ""

    # Probe 2
    cat > "$tmp_dir/p2.txt" <<'EOF'
In a Revit family document, an extrusion 'ext' has been created. Extract the
Reference of the +X face (right face) so it can be used with
familyDoc.FamilyCreate.NewAlignment. Show the geometry-walking code including
how to configure Options so the Reference is non-null.
EOF
    probe_model "$CANDIDATE_TAG" "$tmp_dir/p2.txt" "$tmp_dir/p2_out.txt"
    p2_out=$(probe_2_compute_references "$tmp_dir/p2_out.txt")
    echo "$p2_out"
    p2_score=$(echo "$p2_out" | grep -oE "SCORE=[0-9]+" | tail -1 | cut -d= -f2)
    echo ""

    # Probe 3
    cat > "$tmp_dir/p3.txt" <<'EOF'
I'm calling dim.FamilyLabel = pWidth and getting InvalidOperationException.
What are the actual validity rules for labeling a dimension with a family
parameter? Is there a pre-check method? Show safe validation code.
EOF
    probe_model "$CANDIDATE_TAG" "$tmp_dir/p3.txt" "$tmp_dir/p3_out.txt"
    p3_out=$(probe_3_family_label_validity "$tmp_dir/p3_out.txt")
    echo "$p3_out"
    p3_score=$(echo "$p3_out" | grep -oE "SCORE=[0-9]+" | tail -1 | cut -d= -f2)
    echo ""

    total_score=$((p1_score + p2_score + p3_score))
    echo "=== TOTAL: $total_score / 15 (pass threshold: $PASS_THRESHOLD) ==="
    echo ""

    # Save probe transcripts for inspection
    transcript="$(dirname "$0")/probe_transcript_$(date +%Y%m%d_%H%M%S).md"
    {
        echo "# Probe transcript for $CANDIDATE_TAG"
        echo "Score: $total_score / 15 (threshold: $PASS_THRESHOLD)"
        echo ""
        echo "## Probe 1: Parametric extrusion ($p1_score/5)"
        echo '```csharp'
        cat "$tmp_dir/p1_out.txt"
        echo '```'
        echo ""
        echo "## Probe 2: Face reference extraction ($p2_score/5)"
        echo '```csharp'
        cat "$tmp_dir/p2_out.txt"
        echo '```'
        echo ""
        echo "## Probe 3: FamilyLabel validity ($p3_score/5)"
        echo '```csharp'
        cat "$tmp_dir/p3_out.txt"
        echo '```'
    } > "$transcript"
    echo "Transcript: $transcript"
    echo ""

    if [ "$total_score" -ge "$PASS_THRESHOLD" ]; then
        return 0
    else
        return 1
    fi
}

do_promote() {
    if ! ollama_list_has "$CANDIDATE_TAG"; then
        echo "[ERROR] Cannot promote -- $CANDIDATE_TAG is not in Ollama"
        exit 2
    fi

    if ollama_list_has "$PRODUCTION_TAG"; then
        echo "  Backing up $PRODUCTION_TAG -> $BACKUP_TAG"
        ollama_copy "$PRODUCTION_TAG" "$BACKUP_TAG"
    else
        echo "  No existing $PRODUCTION_TAG -- skipping backup"
    fi

    echo "  Promoting $CANDIDATE_TAG -> $PRODUCTION_TAG"
    ollama_copy "$CANDIDATE_TAG" "$PRODUCTION_TAG"

    echo ""
    echo "[OK] Promoted. Current state:"
    curl -s "$OLLAMA_HOST/api/tags" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for m in d.get('models', []):
    if 'revit-family-engine' in m['name']:
        size_gb = m.get('size', 0) / 1e9
        print(f'  {m[\"name\"]:<42s}  {size_gb:5.2f} GB')
"
    echo ""
    echo "  Rollback command (if v2 misbehaves in production):"
    echo "    ollama cp $BACKUP_TAG $PRODUCTION_TAG"
}

do_rollback() {
    if ! ollama_list_has "$BACKUP_TAG"; then
        echo "[ERROR] Cannot rollback -- $BACKUP_TAG not found"
        echo "        Was promote run before? Check 'ollama list'."
        exit 2
    fi

    echo "  Restoring $BACKUP_TAG -> $PRODUCTION_TAG"
    ollama_copy "$BACKUP_TAG" "$PRODUCTION_TAG"

    echo ""
    echo "[OK] Rolled back. Current state:"
    curl -s "$OLLAMA_HOST/api/tags" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for m in d.get('models', []):
    if 'revit-family-engine' in m['name']:
        size_gb = m.get('size', 0) / 1e9
        print(f'  {m[\"name\"]:<42s}  {size_gb:5.2f} GB')
"
}

# ---- main dispatch ----------------------------------------------------------

cmd="${1:-auto}"

case "$cmd" in
    --probe|probe)
        if run_probes; then
            echo "[PASS] Candidate would be promoted."
            exit 0
        else
            echo "[FAIL] Candidate would NOT be promoted. Review transcript above."
            exit 1
        fi
        ;;

    --promote|promote)
        do_promote
        ;;

    --rollback|rollback)
        do_rollback
        ;;

    auto|"")
        echo "=== Auto mode: probe -> decide ==="
        echo ""
        if run_probes; then
            echo "[PASS] Promoting automatically..."
            echo ""
            do_promote
        else
            echo "[FAIL] Score below threshold. NOT promoting."
            echo "       Options: run with --promote to force, or investigate the transcript."
            exit 1
        fi
        ;;

    -h|--help|help)
        sed -n '2,18p' "$0" | sed 's/^# \?//'
        ;;

    *)
        echo "Unknown command: $cmd"
        echo "Run with --help for usage."
        exit 2
        ;;
esac
