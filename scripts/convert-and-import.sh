#!/usr/bin/env bash
set -u
BASE="${ASTRA_CONVERT_BASE:-$HOME/astra-convert/toolchain}"
OUT="${ASTRA_CONVERT_OUT:-$HOME/astra-convert/result}"
AVATAR="${1:-cyrene}"
CKPT="${2:-$BASE/CyreneV3.7-e25.ckpt}"
PTH="${3:-$BASE/CyreneV3.7_e16_s1392.pth}"
SIMPLIFY="${ASTRA_CONVERT_SIMPLIFY:-0}"
QUANTIZE="${ASTRA_CONVERT_QUANTIZE:-0}"
SCRIPT="$BASE/v1_converter.py"
TEMPLATES="$BASE/templates"
if [ ! -f "$CKPT" ] || [ ! -f "$PTH" ] || [ ! -f "$SCRIPT" ] || [ ! -d "$TEMPLATES" ]; then
  echo "missing converter input/script/templates" >&2; exit 2
fi
mkdir -p "$OUT"
ARGS=(/usr/bin/python3 "$SCRIPT" --ckpt "$CKPT" --pth "$PTH" --shells "$TEMPLATES" --out "$OUT" --clean)
[ "$SIMPLIFY" = 1 ] && ARGS+=(--simplify)
[ "$QUANTIZE" = 1 ] && ARGS+=(--quantize)
printf 'Running:'; printf ' %q' "${ARGS[@]}"; echo
PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8 "${ARGS[@]}"
rc=$?
[ $rc -eq 0 ] || { echo "converter failed: $rc" >&2; exit $rc; }
for f in prompt_encoder.onnx t2s_encoder.onnx t2s_first_stage_decoder.onnx t2s_stage_decoder.onnx vits.onnx; do
  [ -s "$OUT/$f" ] || { echo "missing output: $f" >&2; exit 3; }
done
TARGET="${ASTRA_TTS_HOME:-$HOME/tts-arm64}/resources/models_v1/$AVATAR"
mkdir -p "$TARGET"
cp -f "$OUT"/*.onnx "$TARGET/"
printf 'Imported to %s\n' "$TARGET"
ls -lh "$TARGET"/*.onnx
