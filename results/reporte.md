# Resultados: analista junior vs. IA gratis

Criterio de aprobación (fijado antes de correr): total ≥ 70% y ningún bloque por debajo de 50%.

Visualización e insight de negocio: Claude (IA), a ciegas: respuestas anonimizadas y mezcladas, con la rúbrica y los puntos clave de bench/tasks.py, a pedido de Pablo. No es corrección humana.

| Modelo | SQL | Limpieza | Visualización | Estadística | Insight de negocio | Total | ¿Aprobó? | Tiempo total | Costo |
|---|---|---|---|---|---|---|---|---|---|
| gemini-flash-lite | 100% | 50% | 88% | 100% | 72% | 82% | SÍ | 3 min | USD 0 |
| gemma4-12b | 100% | 10% | 38% | 80% | 50% | 56% | NO | 33 min | USD 0 |
| gpt-oss-120b-groq | 80% | 40% | 57% | 100% | 68% | 69% | NO | 2 min | USD 0 |
| qwen3.5-4b | 30% | 10% | 2% | 10% | 20% | 15% | NO | 23 min | USD 0 |
| qwen3.5-9b | 60% | 0% | 12% | 50% | 38% | 32% | NO | 29 min | USD 0 |

## Fallos de las tareas autocorregidas

### gemini-flash-lite (5 fallos)
- **L02 Provincias normalizadas**: resultado['caba']: esperado 728, recibido 283
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L06 Teléfonos faltantes**: resultado: esperado 400, recibido 241
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 499806.85
- **L08 Join con códigos sucios**: error al ejecutar:     op = _MergeOperation(   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/reshape/merge.py", line 807, in __init__     self._maybe_coerce_merge_keys(

### gemma4-12b (14 fallos)
- **E01 Media y mediana**: error al ejecutar:     frame = _wrap_result(   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/io/sql.py", line 214, in _wrap_result     frame = frame.set_index(index_col)   F
- **E08 Test de independencia**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_leibcnd8/solution.py", line 22, in solve     df = p
- **L01 Clientes únicos**: resultado: esperado 3000, recibido 3235
- **L02 Provincias normalizadas**: resultado['caba']: esperado 728, recibido 283
- **L03 Fechas mezcladas**: error al ejecutar:     return object.__getattribute__(self, name)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/accessor.py", line 224, in __get__     accessor_obj = 
- **L04 Montos en formato argentino**: resultado: esperado 507536291.52, recibido 942.29
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L06 Teléfonos faltantes**: error al ejecutar:     res = mod.solve(data_dir)   File "/tmp/bench_jpir7wi4/solution.py", line 23, in solve     (df['telefono'].astype(str).str.strip().upper() == "NA")   File "/Users/guzzipa/projects/analista-junior-be
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 509611.99
- **L08 Join con códigos sucios**: error al ejecutar:     accessor_obj = self._accessor(obj)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/strings/accessor.py", line 194, in __init__     self._inferred
- **L10 Tabla ancha**: error al ejecutar:     new_values = astype_array(values, dtype, copy=copy)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/dtypes/astype.py", line 182, in astype_array 
- **V04 Distribución del ticket**: error al ejecutar:     mod.solve(data_dir, out_png)   File "/tmp/bench_htftxz6z/solution.py", line 42, in solve     n_bins = min(30, len(df.unique()))   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/pytho
- **V08 Paneles por región**: error al ejecutar:   File "<frozen importlib._bootstrap_external>", line 913, in source_to_code   File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed   File "/tmp/bench_jk2snjmd/solution.py", lin
- **V09 Cohortes**: error al ejecutar:     mod.solve(data_dir, out_png)   File "/tmp/bench_vnfve4us/solution.py", line 59, in solve     im = retention_matrix.iloc[:12, :12].plot(   File "/Users/guzzipa/projects/analista-junior-bench/.venv/l

### gpt-oss-120b-groq (10 fallos)
- **L01 Clientes únicos**: resultado: esperado 3000, recibido 3123
- **L02 Provincias normalizadas**: resultado['caba']: esperado 728, recibido 585
- **L03 Fechas mezcladas**: resultado['2025-07']: esperado 96, recibido 35
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 498793.46
- **L08 Join con códigos sucios**: resultado['belleza']: esperado 22778390.0, recibido 5931830.0
- **S04 Clientes nuevos por mes**: fila 1, columna 2: esperado 1085, recibido 967
- **S10 Recompra a 90 días**: fila 1, columna 1: esperado 0.6378, recibido 0.6329
- **V01 Evolución mensual**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 58, in main     mod.solve(data_dir, out_png)   File "/tmp/bench_qj_qkbmy/solution.py", line 58, in solve     plt
- **V02 Ranking de productos**: error al ejecutar:         WHERE p.estado = 'entregado'           AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'         GROUP BY p.producto_id, pr.nombre         ORDER BY facturacion DESC         LIMIT 10;     ': no 

### qwen3.5-4b (34 fallos)
- **E01 Media y mediana**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_03hkclal/solution.py", line 20, in solve     ticket
- **E02 Test A/B**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_0onk5e28/solution.py", line 50, in solve     z_stat
- **E04 Correlación**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_6br591fg/solution.py", line 6, in solve     db_path
- **E05 Crecimiento interanual**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_lqnt9zmt/solution.py", line 7, in solve     db_path
- **E06 Tendencia lineal**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_j2oigviz/solution.py", line 5, in solve     db_path
- **E07 Percentil 90**: error al ejecutar:     res_values = ops.logical_op(lvalues, rvalues, op)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/ops/array_ops.py", line 454, in logical_op     
- **E08 Test de independencia**: error al ejecutar:     res = mod.solve(data_dir)   File "/tmp/bench_2xyxqnn0/solution.py", line 41, in solve     chi2, p_valor, _, _ = stats.chi2_contingency(contingency_table)   File "/Users/guzzipa/projects/analista-ju
- **E09 Tamaño de muestra**: resultado: esperado 24400, recibido 12200
- **E10 ¿Qué envío devuelve menos?**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_kdtfe6b5/solution.py", line 16, in solve     stats_
- **L01 Clientes únicos**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_ray3toqo/solution.py", line 6, in solve     db_path
- **L02 Provincias normalizadas**: resultado: claves distintas. Faltan ['caba', 'chaco', 'chubut', 'cordoba', 'corrientes', 'entre rios']; sobran []
- **L03 Fechas mezcladas**: resultado['2025-07']: esperado 96, recibido 204
- **L04 Montos en formato argentino**: resultado: esperado 507536291.52, recibido 461820.29
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L06 Teléfonos faltantes**: error al ejecutar:     res = mod.solve(data_dir)   File "/tmp/bench_5eq29_e8/solution.py", line 17, in solve     df_crm = df_crm.str.strip()   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 498793.46
- **L08 Join con códigos sucios**: error al ejecutar:   File "<frozen importlib._bootstrap_external>", line 913, in source_to_code   File "<frozen importlib._bootstrap>", line 228, in _call_with_frames_removed   File "/tmp/bench_sav2p846/solution.py", lin
- **L10 Tabla ancha**: error al ejecutar:     columnas_mensuales = ventas_wide_df[categoria]   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/frame.py", line 4113, in __getitem__     indexer =
- **S02 Top 5 productos**: fila 1, columna 3: esperado 2472, recibido 2388
- **S03 Ticket por canal**: error al ejecutar: no such column: i.facturacion
- **S04 Clientes nuevos por mes**: error al ejecutar: ambiguous column name: cliente_id
- **S07 Facturación acumulada**: esperaba 12 filas, recibió 19
- **S08 Producto estrella por región**: esperaba 6 filas, recibió 210
- **S09 Aprobación de tarjetas**: error al ejecutar: no such column: pago.fecha
- **S10 Recompra a 90 días**: error al ejecutar: no such column: p2.fecha
- **V01 Evolución mensual**: error al ejecutar:         FROM pedidos p         JOIN items i ON p.pedido_id = i.pedido_id         WHERE p.estado = 'entregado'         GROUP BY mes         ORDER BY mes     ': no such column: items.cantidad
- **V03 Mix de canales**: error al ejecutar:     return arrays_to_mgr(arrays, columns, index, dtype=dtype, typ=typ, consolidate=copy)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/internals/co
- **V04 Distribución del ticket**: error al ejecutar:     return object.__getattribute__(self, name)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/accessor.py", line 224, in __get__     accessor_obj = 
- **V05 Región por categoría**: error al ejecutar:     ) = self._get_merge_keys()   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/reshape/merge.py", line 1311, in _get_merge_keys     left_keys.append(
- **V06 Tiempos de entrega**: error al ejecutar:           AND DATE(p.fecha) >= '2026-01-01'            AND DATE(p.fecha) <= '2026-06-30'           AND p.fecha_entrega IS NOT NULL         GROUP BY p.region         ORDER BY p.region     ': no such col
- **V07 Entrega y satisfacción**: error al ejecutar:     f = lambda x: func(x, *args, **kwargs)   File "/tmp/bench_cacq4d8i/solution.py", line 27, in <lambda>     "estado": lambda x: 1 if x == "entregado" else 0, # 1 si entregado, 0 si no   File "/Users/
- **V08 Paneles por región**: error al ejecutar:     indexer = self.columns._get_indexer_strict(key, "columns")[1]   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/indexes/base.py", line 6212, in _ge
- **V09 Cohortes**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 58, in main     mod.solve(data_dir, out_png)   File "/tmp/bench_w7lvvpw_/solution.py", line 103, in solve     to
- **V10 La caída de marzo**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 58, in main     mod.solve(data_dir, out_png)   File "/tmp/bench_lnybzboj/solution.py", line 34, in solve     df_

### qwen3.5-9b (22 fallos)
- **E01 Media y mediana**: resultado['media']: esperado 383213.34, recibido 7565014630.0
- **E04 Correlación**: error al ejecutar:     ) = self._get_merge_keys()   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/reshape/merge.py", line 1311, in _get_merge_keys     left_keys.append(
- **E06 Tendencia lineal**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 60, in main     res = mod.solve(data_dir)   File "/tmp/bench_65ojevpc/solution.py", line 24, in solve     df_men
- **E08 Test de independencia**: error al ejecutar: pandas.errors.DatabaseError: Execution failed on sql '         SELECT c.region, p.medio          FROM pagos p         JOIN pedidos ped ON p.pedido_id = ped.id         JOIN clientes c ON ped.cliente_id 
- **E09 Tamaño de muestra**: resultado: esperado 24400, recibido 20621
- **L01 Clientes únicos**: resultado: esperado 3000, recibido 3235
- **L02 Provincias normalizadas**: resultado['caba']: esperado 728, recibido 283
- **L03 Fechas mezcladas**: resultado['2025-07']: esperado 96, recibido 67
- **L04 Montos en formato argentino**: resultado: esperado 507536291.52, recibido 942.29
- **L05 Export de Excel**: error al ejecutar:   File "pandas/_libs/parsers.pyx", line 574, in pandas._libs.parsers.TextReader.__cinit__   File "pandas/_libs/parsers.pyx", line 663, in pandas._libs.parsers.TextReader._get_header   File "pandas/_lib
- **L06 Teléfonos faltantes**: resultado: esperado 400, recibido 241
- **L07 Pagos de prueba**: resultado: esperado 441547.29, recibido 498793.46
- **L08 Join con códigos sucios**: error al ejecutar:     accessor_obj = self._accessor(obj)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/strings/accessor.py", line 194, in __init__     self._inferred
- **L09 Zonas horarias**: error al ejecutar:     arr = self._data.tz_localize(tz, ambiguous, nonexistent)   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/arrays/_mixins.py", line 81, in method  
- **L10 Tabla ancha**: resultado['belleza']: esperado 211291376, recibido 9223372036854775807
- **S03 Ticket por canal**: fila 1, columna 2: esperado 359228.9, recibido 240496.59
- **S04 Clientes nuevos por mes**: esperaba 12 filas, recibió 18
- **S06 Clientes perdidos**: fila 1, columna 1: esperado 1456, recibido 1426
- **S08 Producto estrella por región**: error al ejecutar: no such column: p.producto_id
- **V01 Evolución mensual**: error al ejecutar:     ax.set_xticklabels([f"{año}-{mes:02d}" for año in facturacion_mensual['Año'].unique()    File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/matplotlib/axes/_base.
- **V06 Tiempos de entrega**: error al ejecutar:     ) = self._get_merge_keys()   File "/Users/guzzipa/projects/analista-junior-bench/.venv/lib/python3.9/site-packages/pandas/core/reshape/merge.py", line 1311, in _get_merge_keys     left_keys.append(
- **V07 Entrega y satisfacción**: error al ejecutar:     main()   File "/Users/guzzipa/projects/analista-junior-bench/bench/_runner.py", line 58, in main     mod.solve(data_dir, out_png)   File "/tmp/bench_u2rmwggx/solution.py", line 64, in solve     z =

