# Resultados: analista junior vs. IA gratis

Criterio de aprobación (fijado antes de correr): total ≥ 70% y ningún bloque por debajo de 50%.

| Modelo | SQL | Limpieza | Visualización | Estadística | Insight de negocio | Total | ¿Aprobó? | Tiempo total | Costo |
|---|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite | 100% | 50% | pendiente | 100% | pendiente | pendiente | pendiente | 3 min | USD 0 |
| gpt-oss-120b-groq | 80% | 40% | pendiente | 100% | pendiente | pendiente | pendiente | 2 min | USD 0 |

Faltan 38 correcciones humanas (o tareas sin correr). Corré `python bench.py review` para completarlas.

## Fallos de las tareas autocorregidas

### gemini-flash-lite (5 fallos)
- **L02 Provincias normalizadas**: resultado['caba']: esperado 728, recibido 283
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L06 Teléfonos faltantes**: resultado: esperado 400, recibido 241
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 499806.85
- **L08 Join con códigos sucios**: error al ejecutar:     op = _MergeOperation(   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/reshape/merge.py", line 807, in __init__     self._maybe_coerce_merge_keys(

### gpt-oss-120b-groq (10 fallos)
- **L01 Clientes únicos**: resultado: esperado 3000, recibido 3123
- **L02 Provincias normalizadas**: no encontré un bloque de código en la respuesta
- **L03 Fechas mezcladas**: resultado['2025-07']: esperado 96, recibido 35
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 498793.46
- **L08 Join con códigos sucios**: resultado['belleza']: esperado 22778390.0, recibido 5931830.0
- **S04 Clientes nuevos por mes**: fila 1, columna 2: esperado 1085, recibido 967
- **S10 Recompra a 90 días**: fila 1, columna 1: esperado 0.6378, recibido 0.6329
- **V01 Evolución mensual**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 58, in main     mod.solve(data_dir, out_png)   File "/tmp/bench_qj_qkbmy/solution.py", line 58, in solve     plt
- **V02 Ranking de productos**: error al ejecutar:         WHERE p.estado = 'entregado'           AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'         GROUP BY p.producto_id, pr.nombre         ORDER BY facturacion DESC         LIMIT 10;     ': no 

