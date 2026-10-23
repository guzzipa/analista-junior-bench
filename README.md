# Analista junior vs. IA gratis

50 tareas reales de un analista de datos junior, corridas con modelos de IA que no cuestan nada (modelos abiertos en tu notebook y capas gratuitas de APIs). Las respuestas se corrigen con código, no a ojo.

## Resultados

_Pendiente: se completa con `python bench.py report` (ver `results/reporte.md`)._

## Qué evalúa

Cinco bloques de 10 tareas cada uno, sobre los datos de **Tienda Pampa**, un e-commerce argentino ficticio:

| Bloque | Qué se pide | Cómo se corrige |
|---|---|---|
| SQL | Consultas sobre la base: facturación, cohortes, ventanas, tasas | Automático: se ejecuta la consulta y se compara el resultado con la respuesta correcta |
| Limpieza | Archivos sucios: duplicados, fechas mezcladas, montos `1.234,50`, export de Excel en latin-1, zonas horarias | Automático: se ejecuta el código y se compara el resultado |
| Estadística | Test A/B, intervalos, correlación, tamaño de muestra, paradoja de Simpson | Automático |
| Visualización | Gráficos para gerentes no técnicos | El código tiene que correr y generar el PNG; la calidad la puntúa una persona del 1 al 5 |
| Insight de negocio | Explicar una caída de ventas, detectar un dato falso, priorizar, resumen para directorio | Puntaje humano del 1 al 5 con puntos clave predefinidos |

Los datos son sintéticos y se generan con una semilla fija, así que cualquiera obtiene exactamente los mismos. Tienen problemas "plantados" a propósito, como en la vida real: un quiebre de stock, un corte del procesador de tarjetas, pedidos de prueba de QA cargados en producción, un día sin datos por una falla del pipeline y un cambio de operador logístico. Como son datos nuevos, ningún modelo pudo haberlos visto durante su entrenamiento.

### Criterio de "aprobó el período de prueba"

Fijado **antes** de correr cualquier modelo (ver `APRUEBA_TOTAL` en `bench/cli.py`):

- Puntaje total de al menos **70%** (promedio de los 5 bloques), y
- ningún bloque por debajo de **50%**.

En los bloques humanos, un puntaje de 1 a 5 se convierte en 0% a 100%. Un gráfico cuyo código no corre vale 0.

### Corrección humana a ciegas

`python bench.py review` muestra las respuestas de gráficos e insights en orden aleatorio y **sin decir qué modelo las escribió**, junto con los puntos clave que tiene que tener una buena respuesta.

## Modelos

Definidos en `models.json`. Para agregar otro, sumá una entrada.

| Nombre | Dónde corre | Tamaño / límite |
|---|---|---|
| qwen3.5-4b | Local (Ollama) | ~3,5 GB |
| qwen3.5-9b | Local (Ollama) | ~7 GB |
| gemma4-12b | Local (Ollama) | ~8 GB |
| gpt-oss-120b-groq | Capa gratuita de Groq | tope diario de tokens: puede llevar 2 días |
| gemini-flash-lite | Capa gratuita de Google AI Studio | |
| gpt-oss-20b (opcional) | Local (Ollama) | ~14 GB, muy justo en 16 GB de RAM |

Todos corren con temperatura 0 y una sola vez por tarea, con el modo de razonamiento que traen por defecto. Los modelos locales tienen un tope de 8.192 tokens y 15 minutos por respuesta: si no terminan, la tarea cuenta como fallida.

## Cómo correrlo (Mac)

```bash
# 1. Entorno de Python
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. Generar datos y chequear que todo funciona (las soluciones de referencia tienen que sacar 100%)
.venv/bin/python bench.py setup
.venv/bin/python bench.py verify

# 3. Modelos locales: instalar Ollama (https://ollama.com o `brew install ollama`) y abrirlo.
#    Este script baja cada modelo, corre las 50 tareas y lo borra para liberar disco.
./run_local.sh

# 4. Modelos por API (claves gratuitas, sin tarjeta)
# Guardalas en un archivo .env en la raíz del repo (está en .gitignore):
#   GROQ_API_KEY=...      # https://console.groq.com/keys
#   GEMINI_API_KEY=...    # https://aistudio.google.com/apikey
.venv/bin/python bench.py run --model gpt-oss-120b-groq
.venv/bin/python bench.py run --model gemini-flash-lite

# 5. Corregir gráficos e insights a ciegas, y armar el reporte
.venv/bin/python bench.py review
.venv/bin/python bench.py report
```

Todo es retomable: si se corta (tope de una API, reinicio), el mismo comando sigue donde quedó. Para repetir una tarea: `--tasks S03 --force`.

Otros comandos: `bench.py list` (tareas y modelos) y `bench.py regrade` (recorrige respuestas guardadas).

## Salidas

- `results/<modelo>/<tarea>.json`: la respuesta completa de cada modelo, el código extraído, el tiempo y la corrección.
- `results/<modelo>/<tarea>.png`: los gráficos que generó cada modelo.
- `results/reporte.md`: tabla de resultados y lista de cada fallo con el motivo.
- `results/resumen.csv` y `results/grafico_resultados.png`.

## Seguridad

El benchmark **ejecuta en tu máquina el código Python que escriben los modelos**. Lo hace en un proceso separado, con límite de tiempo y sobre una copia de los datos, pero no es un sandbox: el código podría, en teoría, acceder a otros archivos. Los modelos solo reciben tareas de análisis de datos; si te preocupa, corrélo en un usuario o una máquina virtual aparte.

## Limitaciones

- Una sola corrida por tarea a temperatura 0: modelos distintos pueden variar entre corridas.
- Los bloques de visualización e insight dependen del criterio de quien corrige. La corrección a ciegas y los puntos clave escritos de antemano reducen ese sesgo, pero no lo eliminan.
- Las tareas están en español. Los modelos chicos suelen rendir algo mejor en inglés.
- Mide tareas de un analista junior en su primera semana, no el trabajo completo de un analista.

## Licencia

MIT
