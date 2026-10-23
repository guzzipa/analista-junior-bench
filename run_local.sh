#!/usr/bin/env bash
# Corre los modelos locales de a uno: descarga, corre las 50 tareas y borra el modelo para liberar disco.
# Uso: ./run_local.sh                      (los 3 modelos locales principales)
#      ./run_local.sh gpt-oss-20b          (uno en particular, por su "name" de models.json)
set -euo pipefail
cd "$(dirname "$0")"
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

MODELOS=("$@")
if [ ${#MODELOS[@]} -eq 0 ]; then
  MODELOS=(qwen3.5-4b qwen3.5-9b gemma4-12b)
fi

for NAME in "${MODELOS[@]}"; do
  TAG=$($PY -c "import json,sys; m={x['name']:x for x in json.load(open('models.json'))['models']}; print(m[sys.argv[1]]['model'])" "$NAME")
  echo "=== $NAME ($TAG) ==="
  ollama pull "$TAG"
  $PY bench.py run --model "$NAME" || echo "!! $NAME terminó con error, sigo con el próximo"
  ollama rm "$TAG"
done
echo "Listo. Siguiente: $PY bench.py review"
