"""Las 50 tareas del benchmark, en 5 bloques de 10.

Cada tarea tiene:
  - kind: "sql" | "python" | "viz" | "text"
  - prompt: lo que ve el modelo
  - ref: solución de referencia (SQL o código Python). El valor esperado se
    calcula ejecutando esta referencia sobre los datos, con el mismo
    ejecutor que corre las respuestas de los modelos.
  - check: cómo se compara la respuesta (solo sql/python)
  - rubric / puntos_clave: para la corrección humana (viz/text)
"""
import os
import sqlite3

SCHEMA = """Base SQLite `tienda.db` de Tienda Pampa (e-commerce argentino). Montos en pesos argentinos corrientes.

- clientes(cliente_id, nombre, email, provincia, region, fecha_alta 'YYYY-MM-DD', segmento)
  region ∈ {AMBA, Centro, Cuyo, NOA, NEA, Patagonia}
- productos(producto_id, nombre, categoria, precio_lista, costo)
  categoria ∈ {Tecnología, Electro, Hogar, Deportes, Moda, Belleza}; precio_lista y costo a valores de enero 2025
- pedidos(pedido_id, cliente_id, fecha 'YYYY-MM-DD', estado, canal, cupon, fecha_entrega)
  estado ∈ {entregado, cancelado, devuelto}; canal ∈ {web, app}; cupon es NULL si no se usó;
  fecha_entrega es NULL si el pedido se canceló
- items(pedido_id, producto_id, cantidad, precio_unitario)   -- precio efectivamente cobrado
- pagos(pedido_id, medio, cuotas, monto, aprobado, fecha)
  medio ∈ {tarjeta, transferencia, billetera}; aprobado ∈ {0,1}; un pedido puede tener más de un intento de pago
- resenas(pedido_id, puntaje, comentario)   -- puntaje de 1 a 5
- sesiones_ab(usuario_id, variante, convirtio, fecha)  -- experimento de checkout de mayo 2026, variante ∈ {A,B}

Definiciones de la empresa: facturación = suma de cantidad × precio_unitario. "Ticket" = facturación de un pedido.
Los datos van del 2025-01-01 al 2026-06-30."""

PY_RULES = """Escribí una función Python `solve(data_dir)` que devuelva el resultado pedido.
- La base está en os.path.join(data_dir, "tienda.db") y los archivos mencionados están en data_dir.
- Podés usar pandas, numpy, scipy, sqlite3 y la librería estándar.
- No imprimas nada, no pidas input y no modifiques los archivos.
- Respondé con UN solo bloque ```python que contenga todo el código (imports incluidos)."""

VIZ_RULES = """Escribí una función Python `solve(data_dir, out_path)` que genere el gráfico con matplotlib
y lo guarde como PNG en out_path (por ejemplo con plt.savefig(out_path, dpi=120, bbox_inches="tight")).
- La base está en os.path.join(data_dir, "tienda.db").
- Podés usar pandas, numpy, matplotlib y la librería estándar (no seaborn ni plotly).
- El gráfico va a ir a una presentación para gerentes que no son técnicos: tiene que entenderse solo.
- Respondé con UN solo bloque ```python que contenga todo el código (imports incluidos)."""

SQL_RULES = """Respondé con UNA sola consulta SQL (dialecto SQLite) dentro de un bloque ```sql.
Devolvé exactamente las columnas pedidas, en ese orden y con esos nombres."""

TEXT_RULES = """Respondé en texto, sin código. Usá solamente los datos que te paso: si algo no se puede saber con
estos datos, decilo."""

VIZ_RUBRIC = """5 = correcto, claro y listo para mostrar a un gerente (tipo de gráfico adecuado, títulos, ejes con unidades, legible).
4 = correcto con detalles menores de presentación.
3 = datos correctos pero tipo de gráfico mejorable o difícil de leer.
2 = errores en los datos o en el cálculo, aunque el gráfico se vea bien.
1 = no responde lo pedido, engañoso o ilegible."""

TEXT_RUBRIC = """5 = identifica todos los puntos clave, cuantifica con los números de las tablas, no inventa nada y propone algo accionable.
4 = identifica los puntos principales con algún detalle menor faltante.
3 = correcto pero genérico, o se le escapa un punto clave importante.
2 = conclusión parcialmente equivocada o con números mal leídos.
1 = conclusión equivocada o inventa datos."""


def _sql(id_, titulo, enunciado, ref, ordered=True, tol=0.01):
    return dict(id=id_, bloque="SQL", kind="sql", titulo=titulo,
                prompt=f"{SCHEMA}\n\nTarea: {enunciado}\n\n{SQL_RULES}",
                ref=ref.strip(), check={"type": "table", "ordered": ordered, "tol": tol})


def _py(id_, bloque, titulo, enunciado, ref, check, files=()):
    return dict(id=id_, bloque=bloque, kind="python", titulo=titulo, files=list(files),
                enunciado=enunciado, ref=ref.strip("\n"), check=check)


def _viz(id_, titulo, enunciado, ref, rubrica):
    return dict(id=id_, bloque="Visualización", kind="viz", titulo=titulo,
                prompt=f"{SCHEMA}\n\nTarea: {enunciado}\n\n{VIZ_RULES}", ref=ref.strip("\n"),
                rubric=VIZ_RUBRIC, puntos_clave=rubrica)


def _txt(id_, titulo, enunciado, contexto_fn, puntos, ref):
    return dict(id=id_, bloque="Insight de negocio", kind="text", titulo=titulo, enunciado=enunciado,
                contexto_fn=contexto_fn, rubric=TEXT_RUBRIC, puntos_clave=puntos, ref=ref.strip())


# =============================================================== BLOQUE 1: SQL
SQL_TASKS = [
    _sql("S01", "Facturación 2025",
         "Calculá la facturación total de los pedidos con estado 'entregado' de 2025. "
         "Una sola columna: facturacion.",
         """SELECT SUM(i.cantidad * i.precio_unitario) AS facturacion
            FROM pedidos p JOIN items i ON i.pedido_id = p.pedido_id
            WHERE p.estado = 'entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'"""),
    _sql("S02", "Top 5 productos",
         "Listá los 5 productos con más unidades vendidas en pedidos entregados de 2025. "
         "Columnas: producto_id, nombre, unidades. Ordenado de mayor a menor por unidades.",
         """SELECT pr.producto_id, pr.nombre, SUM(i.cantidad) AS unidades
            FROM pedidos p JOIN items i ON i.pedido_id = p.pedido_id
            JOIN productos pr ON pr.producto_id = i.producto_id
            WHERE p.estado = 'entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
            GROUP BY pr.producto_id, pr.nombre ORDER BY unidades DESC LIMIT 5"""),
    _sql("S03", "Ticket por canal",
         "Calculá el ticket promedio (facturación promedio por pedido) por canal, para los pedidos entregados "
         "del primer trimestre de 2026. Columnas: canal, ticket_promedio (redondeado a 2 decimales).",
         """SELECT canal, ROUND(AVG(ticket), 2) AS ticket_promedio FROM (
              SELECT p.pedido_id, p.canal, SUM(i.cantidad * i.precio_unitario) AS ticket
              FROM pedidos p JOIN items i ON i.pedido_id = p.pedido_id
              WHERE p.estado = 'entregado' AND p.fecha BETWEEN '2026-01-01' AND '2026-03-31'
              GROUP BY p.pedido_id, p.canal) t
            GROUP BY canal""", ordered=False),
    _sql("S04", "Clientes nuevos por mes",
         "Para cada mes de 2025, contá cuántos clientes hicieron su primera compra ese mes "
         "(primera compra = su primer pedido entregado). Columnas: mes (formato 'YYYY-MM'), nuevos_clientes. "
         "Ordenado por mes.",
         """SELECT substr(primera, 1, 7) AS mes, COUNT(*) AS nuevos_clientes FROM (
              SELECT cliente_id, MIN(fecha) AS primera FROM pedidos WHERE estado = 'entregado' GROUP BY cliente_id) t
            WHERE primera BETWEEN '2025-01-01' AND '2025-12-31'
            GROUP BY mes ORDER BY mes"""),
    _sql("S05", "Tasa de cancelación",
         "Calculá la tasa de cancelación mensual de enero a abril de 2026: pedidos cancelados sobre el total de "
         "pedidos del mes (todos los estados). Columnas: mes ('YYYY-MM'), tasa_cancelacion (fracción entre 0 y 1, "
         "redondeada a 4 decimales). Ordenado por mes.",
         """SELECT substr(fecha, 1, 7) AS mes,
                   ROUND(AVG(CASE WHEN estado = 'cancelado' THEN 1.0 ELSE 0 END), 4) AS tasa_cancelacion
            FROM pedidos WHERE fecha BETWEEN '2026-01-01' AND '2026-04-30'
            GROUP BY mes ORDER BY mes""", tol=0.00011),
    _sql("S06", "Clientes perdidos",
         "¿Cuántos clientes tuvieron al menos un pedido entregado en 2025 y ningún pedido entregado entre el "
         "2026-01-01 y el 2026-06-30? Una sola columna: clientes.",
         """SELECT COUNT(DISTINCT cliente_id) AS clientes FROM pedidos
            WHERE estado = 'entregado' AND fecha BETWEEN '2025-01-01' AND '2025-12-31'
              AND cliente_id NOT IN (SELECT cliente_id FROM pedidos
                                     WHERE estado = 'entregado' AND fecha BETWEEN '2026-01-01' AND '2026-06-30')"""),
    _sql("S07", "Facturación acumulada",
         "Calculá la facturación mensual de 2025 (pedidos entregados) y la facturación acumulada desde enero. "
         "Columnas: mes ('YYYY-MM'), facturacion, acumulado. Ordenado por mes.",
         """WITH m AS (SELECT substr(p.fecha, 1, 7) AS mes, SUM(i.cantidad * i.precio_unitario) AS facturacion
                       FROM pedidos p JOIN items i ON i.pedido_id = p.pedido_id
                       WHERE p.estado = 'entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
                       GROUP BY mes)
            SELECT mes, facturacion, SUM(facturacion) OVER (ORDER BY mes) AS acumulado FROM m ORDER BY mes"""),
    _sql("S08", "Producto estrella por región",
         "Para cada región, encontrá el producto con más unidades vendidas en pedidos entregados de 2025 "
         "(la región es la del cliente). Columnas: region, producto_id, unidades. Ordenado por region.",
         """WITH u AS (SELECT c.region, i.producto_id, SUM(i.cantidad) AS unidades
                       FROM pedidos p JOIN items i ON i.pedido_id = p.pedido_id
                       JOIN clientes c ON c.cliente_id = p.cliente_id
                       WHERE p.estado = 'entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
                       GROUP BY c.region, i.producto_id),
                 r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY region ORDER BY unidades DESC) AS rn FROM u)
            SELECT region, producto_id, unidades FROM r WHERE rn = 1 ORDER BY region"""),
    _sql("S09", "Aprobación de tarjetas",
         "Calculá, para cada día de marzo de 2026, la tasa de aprobación de los intentos de pago con tarjeta "
         "(intentos aprobados sobre intentos totales). Columnas: fecha, tasa_aprobacion (fracción, redondeada a "
         "4 decimales). Ordenado por fecha.",
         """SELECT fecha, ROUND(AVG(aprobado * 1.0), 4) AS tasa_aprobacion FROM pagos
            WHERE medio = 'tarjeta' AND fecha BETWEEN '2026-03-01' AND '2026-03-31'
            GROUP BY fecha ORDER BY fecha""", tol=0.00011),
    _sql("S10", "Recompra a 90 días",
         "Tomá los clientes cuya primera compra (primer pedido entregado) fue en enero de 2025. ¿Qué fracción "
         "de ellos tuvo otro pedido entregado con fecha estrictamente posterior a la primera compra y como máximo "
         "90 días después? Una sola columna: tasa (fracción entre 0 y 1, redondeada a 4 decimales).",
         """WITH f AS (SELECT cliente_id, MIN(fecha) AS primera FROM pedidos WHERE estado = 'entregado'
                       GROUP BY cliente_id),
                 c AS (SELECT * FROM f WHERE primera BETWEEN '2025-01-01' AND '2025-01-31')
            SELECT ROUND(AVG(CASE WHEN EXISTS (
                      SELECT 1 FROM pedidos p WHERE p.cliente_id = c.cliente_id AND p.estado = 'entregado'
                        AND p.fecha > c.primera AND p.fecha <= date(c.primera, '+90 day'))
                   THEN 1.0 ELSE 0 END), 4) AS tasa
            FROM c""", tol=0.00011),
]

# =============================================================== BLOQUE 2: limpieza
PROVINCIAS = ("Buenos Aires, CABA, Catamarca, Chaco, Chubut, Córdoba, Corrientes, Entre Ríos, Formosa, Jujuy, "
              "La Pampa, La Rioja, Mendoza, Misiones, Neuquén, Río Negro, Salta, San Juan, San Luis, Santa Cruz, "
              "Santa Fe, Santiago del Estero, Tierra del Fuego, Tucumán")

CLEAN_TASKS = [
    _py("L01", "Limpieza", "Clientes únicos",
        "El archivo clientes_crm.csv es un export del CRM. Puede tener clientes cargados más de una vez. "
        "¿Cuántos clientes distintos hay? Dos filas son el mismo cliente si tienen el mismo email. "
        "Devolvé un int.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "clientes_crm.csv"), dtype=str, keep_default_na=False)
    return int(df["email"].str.strip().str.lower().nunique())
""", {"type": "int"}, files=["clientes_crm.csv"]),

    _py("L02", "Limpieza", "Provincias normalizadas",
        "En clientes_crm.csv la columna provincia está escrita de muchas formas. Normalizala a la lista oficial: "
        f"{PROVINCIAS}. Devolvé un dict {{provincia_oficial: cantidad_de_filas}} contando todas las filas del "
        "archivo (sin deduplicar) e incluyendo solo las provincias que aparecen.",
        """
import os
import unicodedata
import pandas as pd

MAPA = {
    "caba": "CABA", "capital federal": "CABA", "c.a.b.a.": "CABA", "ciudad de buenos aires": "CABA",
    "buenos aires": "Buenos Aires", "bs as": "Buenos Aires", "pcia. de buenos aires": "Buenos Aires",
    "bs. as.": "Buenos Aires", "cordoba": "Córdoba", "cba": "Córdoba", "santa fe": "Santa Fe",
    "sta fe": "Santa Fe", "entre rios": "Entre Ríos", "e. rios": "Entre Ríos", "mendoza": "Mendoza",
    "mza": "Mendoza", "san juan": "San Juan", "san luis": "San Luis", "tucuman": "Tucumán",
    "salta": "Salta", "jujuy": "Jujuy", "corrientes": "Corrientes", "ctes": "Corrientes",
    "misiones": "Misiones", "chaco": "Chaco", "neuquen": "Neuquén", "nqn": "Neuquén",
    "rio negro": "Río Negro", "r. negro": "Río Negro", "chubut": "Chubut",
}

def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "clientes_crm.csv"), dtype=str, keep_default_na=False)
    return df["provincia"].map(lambda s: MAPA[norm(s)]).value_counts().to_dict()
""", {"type": "dict", "values": {"type": "int"}}, files=["clientes_crm.csv"]),

    _py("L03", "Limpieza", "Fechas mezcladas",
        "En clientes_crm.csv la columna fecha_alta viene en varios formatos (el sistema es argentino: cuando hay "
        "día y mes, el día va primero). Contá cuántas altas hubo en cada mes de 2025, sobre todas las filas del "
        "archivo. Devolvé un dict {'YYYY-MM': cantidad} solo con los meses de 2025.",
        """
import os
import datetime as dt
import pandas as pd

def parse(s):
    s = s.strip()
    if "/" in s:
        return dt.datetime.strptime(s, "%d/%m/%Y").date()
    a = s.split("-")
    if len(a[0]) == 4:
        return dt.date(int(a[0]), int(a[1]), int(a[2]))
    return dt.date(2000 + int(a[2]), int(a[1]), int(a[0]))

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "clientes_crm.csv"), dtype=str, keep_default_na=False)
    f = df["fecha_alta"].map(parse)
    meses = [d.strftime("%Y-%m") for d in f if d.year == 2025]
    return pd.Series(meses).value_counts().to_dict()
""", {"type": "dict", "values": {"type": "int"}}, files=["clientes_crm.csv"]),

    _py("L04", "Limpieza", "Montos en formato argentino",
        "En clientes_crm.csv la columna monto_compras tiene montos en pesos escritos a mano. Convertila a número "
        "y devolvé la suma total redondeada a 2 decimales (float), sobre todas las filas del archivo.",
        """
import os
import pandas as pd

def parse(s):
    s = s.replace("$", "").strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "clientes_crm.csv"), dtype=str, keep_default_na=False)
    return round(float(df["monto_compras"].map(parse).sum()), 2)
""", {"type": "number", "tol": 0.02, "rel": 1e-9}, files=["clientes_crm.csv"]),

    _py("L05", "Limpieza", "Export de Excel",
        "ventas_sucursales.csv es un export de Excel que mandó el área comercial. Calculá la venta total del "
        "primer trimestre de 2026 por sucursal. Devolvé un dict {nombre_de_sucursal: total} con totales "
        "redondeados a 2 decimales.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "ventas_sucursales.csv"), sep=";", encoding="latin-1",
                     decimal=",", thousands=".")
    return {k: round(float(v), 2) for k, v in df.groupby("sucursal")["venta"].sum().items()}
""", {"type": "dict", "values": {"type": "number", "tol": 0.02, "rel": 1e-9}}, files=["ventas_sucursales.csv"]),

    _py("L06", "Limpieza", "Teléfonos faltantes",
        "En clientes_crm.csv, ¿cuántas filas no tienen un teléfono válido cargado? Contá todas las filas del "
        "archivo. Devolvé un int.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "clientes_crm.csv"), dtype=str, keep_default_na=False)
    t = df["telefono"].str.strip().str.lower()
    return int(t.isin(["", "na", "-", "sin dato"]).sum())
""", {"type": "int"}, files=["clientes_crm.csv"]),

    _py("L07", "Limpieza", "Pagos de prueba",
        "Calculá el monto promedio de los pagos aprobados (tabla pagos) de mayo de 2026. Ojo: el equipo de QA "
        "cargó pagos de prueba en producción ese mes y hay que excluirlos. Devolvé un float redondeado a 2 "
        "decimales.",
        """
import os
import sqlite3
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT pa.monto FROM pagos pa JOIN pedidos p ON p.pedido_id = pa.pedido_id
                          JOIN clientes c ON c.cliente_id = p.cliente_id
                          WHERE pa.aprobado = 1 AND pa.fecha BETWEEN '2026-05-01' AND '2026-05-31'
                            AND c.nombre <> 'QA TEST'\"\"\", con)
    return round(float(df["monto"].mean()), 2)
""", {"type": "number", "tol": 0.02, "rel": 1e-9}),

    _py("L08", "Limpieza", "Join con códigos sucios",
        "items_raw.csv es una muestra de líneas de pedido que vino de otro sistema: la columna producto tiene el "
        "código de producto escrito de formas distintas. Cruzala con la tabla productos de tienda.db y devolvé la "
        "facturación (cantidad × precio_unitario) por categoría: dict {categoria: total} redondeado a 2 decimales.",
        """
import os
import re
import sqlite3
import pandas as pd

def solve(data_dir):
    it = pd.read_csv(os.path.join(data_dir, "items_raw.csv"), dtype={"producto": str})
    it["producto_id"] = it["producto"].map(lambda s: int(re.sub(r"\\D", "", s)))
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    pr = pd.read_sql("SELECT producto_id, categoria FROM productos", con)
    m = it.merge(pr, on="producto_id", how="left")
    m["fact"] = m["cantidad"] * m["precio_unitario"]
    return {k: round(float(v), 2) for k, v in m.groupby("categoria")["fact"].sum().items()}
""", {"type": "dict", "values": {"type": "number", "tol": 0.02, "rel": 1e-9}}, files=["items_raw.csv"]),

    _py("L09", "Limpieza", "Zonas horarias",
        "eventos.csv tiene eventos de la app con timestamp en UTC. El negocio reporta por día en hora de Argentina "
        "(UTC-3). Devolvé un dict {'YYYY-MM-DD': cantidad_de_eventos} por día en hora argentina.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "eventos.csv"))
    ts = pd.to_datetime(df["timestamp_utc"], utc=True).dt.tz_convert("America/Argentina/Buenos_Aires")
    return ts.dt.strftime("%Y-%m-%d").value_counts().to_dict()
""", {"type": "dict", "values": {"type": "int"}}, files=["eventos.csv"]),

    _py("L10", "Limpieza", "Tabla ancha",
        "ventas_wide.csv tiene una fila por categoría y una columna por mes de 2025, con montos en pesos. "
        "Devolvé un dict {categoria: venta_total_2025} con los totales como int.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "ventas_wide.csv"), dtype=str)
    long = df.melt(id_vars="categoria", var_name="mes", value_name="venta")
    long["venta"] = long["venta"].str.replace("$", "", regex=False).str.replace(".", "", regex=False) \\
        .str.replace(",", ".", regex=False).str.strip().astype(float)
    return {k: int(round(v)) for k, v in long.groupby("categoria")["venta"].sum().items()}
""", {"type": "dict", "values": {"type": "number", "tol": 1.01, "rel": 1e-12}}, files=["ventas_wide.csv"]),
]

# =============================================================== BLOQUE 3: visualización
VIZ_TASKS = [
    _viz("V01", "Evolución mensual",
         "Graficá la evolución de la facturación mensual (pedidos entregados) de enero 2025 a junio 2026.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT substr(p.fecha,1,7) mes, SUM(i.cantidad*i.precio_unitario)/1e6 f
                          FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado'
                          GROUP BY mes ORDER BY mes\"\"\", con)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.plot(df["mes"], df["f"], marker="o", color="#1f6f8b")
    ax.set_title("Facturación mensual (pedidos entregados)")
    ax.set_ylabel("Millones de ARS corrientes")
    ax.tick_params(axis="x", rotation=60)
    ax.grid(alpha=0.3)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Línea temporal con los 18 meses en orden", "Eje Y con unidades (pesos, idealmente en millones)",
      "Se ven el pico de diciembre 2025, el Hot Sale de mayo y la caída de marzo 2026",
      "Bonus: aclara que son pesos corrientes (con inflación)"]),
    _viz("V02", "Ranking de productos",
         "Mostrá los 10 productos con mayor facturación de 2025 (pedidos entregados).",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT pr.nombre, SUM(i.cantidad*i.precio_unitario)/1e6 f
                          FROM pedidos p JOIN items i USING(pedido_id) JOIN productos pr USING(producto_id)
                          WHERE p.estado='entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
                          GROUP BY pr.nombre ORDER BY f DESC LIMIT 10\"\"\", con)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(df["nombre"][::-1], df["f"][::-1], color="#1f6f8b")
    ax.set_title("Top 10 productos por facturación 2025")
    ax.set_xlabel("Millones de ARS")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Barras horizontales (los nombres son largos) ordenadas de mayor a menor",
      "Solo 2025 y pedidos entregados", "Nombres de producto legibles, eje con unidades"]),
    _viz("V03", "Mix de canales",
         "Mostrá cómo cambió la participación de cada canal (web y app) en la cantidad de pedidos, mes a mes, "
         "de enero 2025 a junio 2026.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql("SELECT substr(fecha,1,7) mes, canal, COUNT(*) n FROM pedidos GROUP BY mes, canal", con)
    pv = df.pivot(index="mes", columns="canal", values="n")
    sh = pv.div(pv.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.stackplot(sh.index, sh["app"], sh["web"], labels=["App", "Web"], colors=["#1f6f8b", "#c9d6df"])
    ax.set_ylim(0, 100); ax.set_ylabel("% de pedidos"); ax.legend(loc="upper left")
    ax.set_title("Participación de canales en los pedidos")
    ax.tick_params(axis="x", rotation=60)
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Participación en % (100% apilado o línea de share), no cantidades absolutas",
      "Se ve que la app crece", "Leyenda clara de qué color es cada canal"]),
    _viz("V04", "Distribución del ticket",
         "Mostrá la distribución del ticket por pedido entregado de 2025.",
         """
import os, sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT p.pedido_id, SUM(i.cantidad*i.precio_unitario)/1e3 t
                          FROM pedidos p JOIN items i USING(pedido_id)
                          WHERE p.estado='entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
                          GROUP BY p.pedido_id\"\"\", con)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(df["t"], bins=np.logspace(np.log10(df["t"].min()), np.log10(df["t"].max()), 40), color="#1f6f8b")
    ax.set_xscale("log")
    ax.axvline(df["t"].median(), color="k", ls="--", label=f"Mediana: {df['t'].median():,.0f} mil ARS")
    ax.set_xlabel("Ticket por pedido (miles de ARS, escala log)"); ax.set_ylabel("Pedidos")
    ax.set_title("Distribución del ticket 2025"); ax.legend()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Histograma (o similar) del ticket por PEDIDO, no por línea de item",
      "Maneja la asimetría (escala log, recorte explícito o anotación); no queda todo en una sola barra",
      "Marca la mediana o el promedio con su valor"]),
    _viz("V05", "Región por categoría",
         "Mostrá la facturación de 2025 (pedidos entregados) cruzando región del cliente y categoría de producto, "
         "de forma que se pueda comparar qué categorías pesan más en cada región.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT c.region, pr.categoria, SUM(i.cantidad*i.precio_unitario) f
                          FROM pedidos p JOIN items i USING(pedido_id) JOIN productos pr USING(producto_id)
                          JOIN clientes c USING(cliente_id)
                          WHERE p.estado='entregado' AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31'
                          GROUP BY c.region, pr.categoria\"\"\", con)
    pv = df.pivot(index="region", columns="categoria", values="f")
    sh = pv.div(pv.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(9, 4.5))
    im = ax.imshow(sh.values, cmap="Blues")
    ax.set_xticks(range(len(sh.columns))); ax.set_xticklabels(sh.columns, rotation=30)
    ax.set_yticks(range(len(sh.index))); ax.set_yticklabels(sh.index)
    for r in range(sh.shape[0]):
        for c in range(sh.shape[1]):
            ax.text(c, r, f"{sh.values[r, c]:.0f}%", ha="center", va="center", fontsize=8)
    ax.set_title("Peso de cada categoría en la facturación de cada región (2025)")
    fig.colorbar(im, label="% de la facturación de la región")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Normaliza dentro de cada región (porcentajes), porque AMBA es mucho más grande",
      "Heatmap anotado o barras 100% apiladas; legible", "Etiquetas de región y categoría visibles"]),
    _viz("V06", "Tiempos de entrega",
         "Compará los días de entrega (fecha_entrega menos fecha del pedido) entre regiones, para pedidos "
         "entregados de 2026.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT c.region, julianday(p.fecha_entrega) - julianday(p.fecha) dias
                          FROM pedidos p JOIN clientes c USING(cliente_id)
                          WHERE p.estado='entregado' AND p.fecha >= '2026-01-01'\"\"\", con)
    orden = df.groupby("region")["dias"].median().sort_values().index
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.boxplot([df.loc[df.region == r, "dias"] for r in orden])
    ax.set_xticks(range(1, len(orden) + 1)); ax.set_xticklabels(orden)
    ax.set_ylabel("Días de entrega"); ax.set_title("Días de entrega por región (2026)")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Muestra la distribución (boxplot/violín) o al menos promedio con dispersión",
      "Regiones ordenadas o fáciles de comparar", "Se ve que Patagonia es la más lenta"]),
    _viz("V07", "Entrega y satisfacción",
         "Mostrá la relación entre los días de entrega y el puntaje de las reseñas.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT CAST(julianday(p.fecha_entrega) - julianday(p.fecha) AS INT) dias, r.puntaje
                          FROM resenas r JOIN pedidos p USING(pedido_id)\"\"\", con)
    g = df.groupby("dias")["puntaje"].agg(["mean", "count"])
    g = g[g["count"] >= 30]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(g.index, g["mean"], color="#1f6f8b")
    ax.set_ylim(1, 5); ax.set_xlabel("Días de entrega"); ax.set_ylabel("Puntaje promedio (1 a 5)")
    ax.set_title("A más días de entrega, peores reseñas")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Agrega por días de entrega (promedio por día) o usa jitter: un scatter crudo de 1-5 no se lee",
      "Se ve la relación negativa", "Título que comunica la conclusión o ejes claros"]),
    _viz("V08", "Paneles por región",
         "Mostrá la evolución mensual de la facturación (pedidos entregados) de cada región, enero 2025 a junio 2026, "
         "de forma que se pueda comparar la tendencia de cada una aunque tengan tamaños muy distintos.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT c.region, substr(p.fecha,1,7) mes, SUM(i.cantidad*i.precio_unitario)/1e6 f
                          FROM pedidos p JOIN items i USING(pedido_id) JOIN clientes c USING(cliente_id)
                          WHERE p.estado='entregado' GROUP BY c.region, mes ORDER BY mes\"\"\", con)
    regs = sorted(df.region.unique())
    fig, axes = plt.subplots(2, 3, figsize=(12, 6), sharex=True)
    for ax, r in zip(axes.flat, regs):
        d = df[df.region == r]
        ax.plot(d["mes"], d["f"], color="#1f6f8b"); ax.set_title(r)
        ax.tick_params(axis="x", rotation=90, labelsize=6)
    fig.suptitle("Facturación mensual por región (millones de ARS, escala propia por panel)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Small multiples (un panel por región) con escala Y propia, o índice base 100",
      "No es una sola línea por región en el mismo eje donde las chicas quedan aplastadas",
      "Títulos por panel y aclaración de unidades"]),
    _viz("V09", "Cohortes",
         "Armá un gráfico de cohortes de retención: clientes agrupados por el mes de su primer pedido entregado "
         "(enero a diciembre 2025) y, para cada mes posterior, qué porcentaje de la cohorte volvió a tener un "
         "pedido entregado.",
         """
import os, sqlite3
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql("SELECT cliente_id, substr(fecha,1,7) mes FROM pedidos WHERE estado='entregado'", con)
    df["m"] = pd.PeriodIndex(df["mes"], freq="M")
    first = df.groupby("cliente_id")["m"].min().rename("coh")
    df = df.join(first, on="cliente_id")
    df = df[(df.coh >= pd.Period("2025-01", "M")) & (df.coh <= pd.Period("2025-12", "M"))]
    df["k"] = (df["m"] - df["coh"]).apply(lambda x: x.n)
    size = df.groupby("coh")["cliente_id"].nunique()
    act = df[df.k > 0].groupby(["coh", "k"])["cliente_id"].nunique().unstack()
    ret = act.div(size, axis=0) * 100
    fig, ax = plt.subplots(figsize=(11, 5))
    im = ax.imshow(ret.values, cmap="Blues", aspect="auto")
    ax.set_yticks(range(len(ret.index))); ax.set_yticklabels([str(p) for p in ret.index])
    ax.set_xticks(range(len(ret.columns))); ax.set_xticklabels(ret.columns)
    ax.set_xlabel("Meses desde la primera compra"); ax.set_ylabel("Cohorte (mes de primera compra)")
    ax.set_title("Retención por cohorte: % de clientes que volvió a comprar")
    fig.colorbar(im, label="% de la cohorte")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Matriz/triángulo de cohortes: filas = cohorte, columnas = meses desde la primera compra",
      "Valores en % del tamaño de la cohorte", "Ejes explicados; idealmente valores anotados o barra de color"]),
    _viz("V10", "La caída de marzo",
         "El directorio quiere entender con UN gráfico qué explica la caída de facturación de marzo 2026 contra "
         "febrero 2026. Elegí vos qué mostrar.",
         """
import os, sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def solve(data_dir, out_path):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT substr(p.fecha,1,7) mes, pr.categoria, SUM(i.cantidad*i.precio_unitario)/1e6 f
                          FROM pedidos p JOIN items i USING(pedido_id) JOIN productos pr USING(producto_id)
                          WHERE p.estado='entregado' AND p.fecha BETWEEN '2026-02-01' AND '2026-03-31'
                          GROUP BY mes, pr.categoria\"\"\", con)
    pv = df.pivot(index="categoria", columns="mes", values="f").fillna(0)
    delta = (pv["2026-03"] - pv["2026-02"]).sort_values()
    feb, mar = pv["2026-02"].sum(), pv["2026-03"].sum()
    labels = ["Febrero"] + list(delta.index) + ["Marzo"]
    fig, ax = plt.subplots(figsize=(10, 5))
    run = feb
    ax.bar(0, feb, color="#7f8c8d")
    for k, (cat, d) in enumerate(delta.items(), start=1):
        ax.bar(k, abs(d), bottom=min(run, run + d), color="#2e8b57" if d >= 0 else "#c0392b")
        ax.text(k, max(run, run + d) + 5, f"{d:+.0f}", ha="center", fontsize=8)
        run += d
    ax.bar(len(labels) - 1, mar, color="#7f8c8d")
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=30)
    ax.set_ylabel("Millones de ARS"); ax.set_ylim(feb * 0.6, feb * 1.05)
    ax.set_title("Qué explica la caída de marzo: casi todo es Tecnología")
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
""", ["Descompone la variación feb → mar (cascada/waterfall o barras de diferencia por categoría o causa)",
      "Hace evidente que Tecnología (quiebre de stock del Celular Nova X) explica la mayor parte",
      "Bonus: muestra también el impacto del corte de pagos con tarjeta",
      "Título que comunica la conclusión, no solo 'Facturación por categoría'"]),
]

# =============================================================== BLOQUE 4: estadística
STATS_TASKS = [
    _py("E01", "Estadística", "Media y mediana",
        "Calculá la media y la mediana del ticket (facturación por pedido) de los pedidos entregados de 2025. "
        "Devolvé un dict {'media': float, 'mediana': float} redondeados a 2 decimales.",
        """
import os, sqlite3
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    t = pd.read_sql(\"\"\"SELECT p.pedido_id, SUM(i.cantidad*i.precio_unitario) t FROM pedidos p
                         JOIN items i USING(pedido_id) WHERE p.estado='entregado'
                         AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY p.pedido_id\"\"\", con)["t"]
    return {"media": round(float(t.mean()), 2), "mediana": round(float(t.median()), 2)}
""", {"type": "dict", "values": {"type": "number", "tol": 0.02, "rel": 1e-9}}),

    _py("E02", "Estadística", "Test A/B",
        "Analizá el experimento de checkout de la tabla sesiones_ab. Calculá la tasa de conversión de cada variante "
        "y el p-valor de un test de diferencia de proporciones de dos colas (test z, o chi-cuadrado equivalente). "
        "Devolvé un dict {'tasa_A': float, 'tasa_B': float, 'p_valor': float, 'significativo': bool} donde "
        "significativo indica si la diferencia es significativa al 5%. Tasas como fracción.",
        """
import os, sqlite3
import numpy as np
import pandas as pd
from scipy import stats

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql("SELECT variante, convirtio FROM sesiones_ab", con)
    g = df.groupby("variante")["convirtio"].agg(["sum", "count"])
    xa, na = g.loc["A"]; xb, nb = g.loc["B"]
    pa, pb = xa / na, xb / nb
    pp = (xa + xb) / (na + nb)
    z = (pb - pa) / np.sqrt(pp * (1 - pp) * (1 / na + 1 / nb))
    p = 2 * stats.norm.sf(abs(z))
    return {"tasa_A": float(pa), "tasa_B": float(pb), "p_valor": float(p), "significativo": bool(p < 0.05)}
""", {"type": "dict", "fields": {"tasa_A": {"type": "number", "tol": 1e-4}, "tasa_B": {"type": "number", "tol": 1e-4},
                                  "p_valor": {"type": "number", "tol": 0.003}, "significativo": {"type": "bool"}}}),

    _py("E03", "Estadística", "Intervalo de confianza",
        "Calculá el intervalo de confianza del 95% para el puntaje promedio de las reseñas (tabla resenas), usando "
        "la distribución t. Devolvé una lista [limite_inferior, limite_superior] redondeados a 4 decimales.",
        """
import os, sqlite3
import numpy as np
import pandas as pd
from scipy import stats

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    x = pd.read_sql("SELECT puntaje FROM resenas", con)["puntaje"].astype(float)
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(0.975, len(x) - 1) * se
    return [round(float(m - h), 4), round(float(m + h), 4)]
""", {"type": "list", "ordered": True, "items": {"type": "number", "tol": 0.0006}}),

    _py("E04", "Estadística", "Correlación",
        "Calculá la correlación de Pearson entre los días de entrega (fecha_entrega menos fecha del pedido) y el "
        "puntaje de la reseña, para los pedidos que tienen reseña. Devolvé un float redondeado a 3 decimales.",
        """
import os, sqlite3
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT julianday(p.fecha_entrega) - julianday(p.fecha) dias, r.puntaje
                          FROM resenas r JOIN pedidos p USING(pedido_id)\"\"\", con)
    return round(float(df["dias"].corr(df["puntaje"])), 3)
""", {"type": "number", "tol": 0.0015}),

    _py("E05", "Estadística", "Crecimiento interanual",
        "Calculá el crecimiento interanual de la facturación (pedidos entregados) del primer trimestre de 2026 "
        "contra el primer trimestre de 2025. Devolvé la variación como fracción (por ejemplo 0.25 = +25%), "
        "redondeada a 4 decimales.",
        """
import os, sqlite3
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    q = \"\"\"SELECT SUM(i.cantidad*i.precio_unitario) f FROM pedidos p JOIN items i USING(pedido_id)
             WHERE p.estado='entregado' AND p.fecha BETWEEN ? AND ?\"\"\"
    a = pd.read_sql(q, con, params=("2025-01-01", "2025-03-31"))["f"][0]
    b = pd.read_sql(q, con, params=("2026-01-01", "2026-03-31"))["f"][0]
    return round(float(b / a - 1), 4)
""", {"type": "number", "tol": 0.00015}),

    _py("E06", "Estadística", "Tendencia lineal",
        "Ajustá una regresión lineal por mínimos cuadrados de la facturación mensual de 2025 (pedidos entregados) "
        "contra el número de mes (1 = enero, ..., 12 = diciembre). Devolvé la pendiente (pesos por mes) como float "
        "redondeado a 0 decimales.",
        """
import os, sqlite3
import numpy as np
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT CAST(substr(p.fecha,6,2) AS INT) m, SUM(i.cantidad*i.precio_unitario) f
                          FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado'
                          AND p.fecha BETWEEN '2025-01-01' AND '2025-12-31' GROUP BY m\"\"\", con)
    return float(round(np.polyfit(df["m"], df["f"], 1)[0]))
""", {"type": "number", "tol": 1.0, "rel": 1e-6}),

    _py("E07", "Estadística", "Percentil 90",
        "Calculá el percentil 90 de los días de entrega (fecha_entrega menos fecha) por región, para los pedidos "
        "entregados de todo el período. Usá interpolación lineal (el método por defecto de numpy y pandas). "
        "Devolvé un dict {region: p90} redondeado a 2 decimales.",
        """
import os, sqlite3
import pandas as pd

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT c.region, julianday(p.fecha_entrega) - julianday(p.fecha) dias
                          FROM pedidos p JOIN clientes c USING(cliente_id) WHERE p.estado='entregado'\"\"\", con)
    return {k: round(float(v), 2) for k, v in df.groupby("region")["dias"].quantile(0.9).items()}
""", {"type": "dict", "values": {"type": "number", "tol": 0.011}}),

    _py("E08", "Estadística", "Test de independencia",
        "¿El medio de pago depende de la región? Hacé un test chi-cuadrado de independencia entre la región del "
        "cliente y el medio de pago, usando todas las filas de la tabla pagos. Devolvé un dict "
        "{'chi2': float, 'p_valor': float, 'significativo': bool} (significativo al 5%).",
        """
import os, sqlite3
import pandas as pd
from scipy import stats

def solve(data_dir):
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    df = pd.read_sql(\"\"\"SELECT c.region, pa.medio FROM pagos pa JOIN pedidos p USING(pedido_id)
                          JOIN clientes c USING(cliente_id)\"\"\", con)
    chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(df["region"], df["medio"]))
    return {"chi2": float(chi2), "p_valor": float(p), "significativo": bool(p < 0.05)}
""", {"type": "dict", "fields": {"chi2": {"type": "number", "tol": 0.05, "rel": 1e-3},
                                  "p_valor": {"type": "number", "tol": 0.005}, "significativo": {"type": "bool"}}}),

    _py("E09", "Estadística", "Tamaño de muestra",
        "Producto quiere repetir un test de checkout. La conversión actual es 3,8% y quieren poder detectar una "
        "mejora a 4,3%, con significancia de 5% (dos colas) y potencia de 80%. ¿Cuántos usuarios hacen falta por "
        "variante? Devolvé un int (redondeá hacia arriba).",
        """
import math
from scipy import stats

def solve(data_dir):
    p1, p2 = 0.038, 0.043
    za, zb = stats.norm.ppf(0.975), stats.norm.ppf(0.80)
    pb = (p1 + p2) / 2
    n = (za * math.sqrt(2 * pb * (1 - pb)) + zb * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / (p2 - p1) ** 2
    return int(math.ceil(n))
""", {"type": "number", "tol": 0, "rel": 0.03}),

    _py("E10", "Estadística", "¿Qué envío devuelve menos?",
        "devoluciones_envio.csv tiene envíos con su método (Moto o Correo), el segmento (AMBA o Interior) y si el "
        "pedido se devolvió (1/0). Calculá la tasa de devolución global de cada método y decí qué método tiene "
        "menor tasa de devolución globalmente, dentro de AMBA y dentro de Interior. Devolvé un dict "
        "{'tasa_moto': float, 'tasa_correo': float, 'mejor_global': str, 'mejor_amba': str, 'mejor_interior': str} "
        "con tasas como fracción y los 'mejor_*' como 'Moto' o 'Correo'.",
        """
import os
import pandas as pd

def solve(data_dir):
    df = pd.read_csv(os.path.join(data_dir, "devoluciones_envio.csv"))
    g = df.groupby("metodo")["devuelto"].mean()
    s = df.groupby(["segmento", "metodo"])["devuelto"].mean()
    return {"tasa_moto": float(g["Moto"]), "tasa_correo": float(g["Correo"]),
            "mejor_global": g.idxmin(), "mejor_amba": s["AMBA"].idxmin(), "mejor_interior": s["Interior"].idxmin()}
""", {"type": "dict", "fields": {"tasa_moto": {"type": "number", "tol": 1e-4},
                                  "tasa_correo": {"type": "number", "tol": 1e-4},
                                  "mejor_global": {"type": "str"}, "mejor_amba": {"type": "str"},
                                  "mejor_interior": {"type": "str"}}}, files=["devoluciones_envio.csv"]),
]


# =============================================================== BLOQUE 5: insight (contextos)
def _q(data_dir, sql, params=()):
    import pandas as pd
    con = sqlite3.connect(os.path.join(data_dir, "tienda.db"))
    try:
        return pd.read_sql(sql, con, params=params)
    finally:
        con.close()


def md(df, floatfmt="{:,.1f}"):
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append(floatfmt.format(v))
            else:
                cells.append(str(v))
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


FACT = "SUM(i.cantidad*i.precio_unitario)"


def ctx_marzo(d):
    a = _q(d, f"""SELECT pr.categoria, substr(p.fecha,1,7) mes, {FACT}/1e6 f FROM pedidos p JOIN items i USING(pedido_id)
                 JOIN productos pr USING(producto_id) WHERE p.estado='entregado'
                 AND (p.fecha BETWEEN '2025-02-01' AND '2025-03-31' OR p.fecha BETWEEN '2026-02-01' AND '2026-03-31')
                 GROUP BY 1,2""").pivot(index="categoria", columns="mes", values="f").reset_index()
    a.columns = ["categoria"] + [f"{c} (M ARS)" for c in a.columns[1:]]
    b = _q(d, """SELECT fecha, ROUND(AVG(aprobado)*100,1) AS pct_aprobacion_tarjeta, COUNT(*) AS intentos
                 FROM pagos WHERE medio='tarjeta' AND fecha BETWEEN '2026-03-01' AND '2026-03-31' GROUP BY fecha""")
    c = _q(d, """SELECT substr(p.fecha,1,7) mes, pr.nombre, SUM(i.cantidad) unidades FROM pedidos p JOIN items i USING(pedido_id)
                 JOIN productos pr USING(producto_id) WHERE p.estado='entregado' AND pr.categoria='Tecnología'
                 AND p.fecha BETWEEN '2026-01-01' AND '2026-04-30' GROUP BY 1,2""").pivot(
        index="nombre", columns="mes", values="unidades").fillna(0).astype(int).reset_index()
    e = _q(d, """SELECT substr(fecha,1,7) mes, estado, COUNT(*) n FROM pedidos WHERE fecha BETWEEN '2026-01-01'
                 AND '2026-04-30' GROUP BY 1,2""").pivot(index="mes", columns="estado", values="n").reset_index()
    return ("Facturación por categoría (pedidos entregados), febrero y marzo de 2025 y 2026, en millones de pesos:\n"
            + md(a) + "\n\nUnidades vendidas de productos de Tecnología por mes (2026):\n" + md(c)
            + "\n\nPedidos por estado y mes (2026):\n" + md(e)
            + "\n\nAprobación diaria de pagos con tarjeta, marzo 2026:\n" + md(b))


def ctx_patagonia(d):
    a = _q(d, """SELECT c.region, substr(p.fecha,1,7) mes, ROUND(AVG(r.puntaje),2) puntaje FROM resenas r
                 JOIN pedidos p USING(pedido_id) JOIN clientes c USING(cliente_id)
                 WHERE p.fecha >= '2026-01-01' GROUP BY 1,2""").pivot(index="region", columns="mes",
                                                                       values="puntaje").reset_index()
    b = _q(d, """SELECT c.region, substr(p.fecha,1,7) mes,
                 ROUND(AVG(julianday(p.fecha_entrega)-julianday(p.fecha)),1) dias FROM pedidos p
                 JOIN clientes c USING(cliente_id) WHERE p.estado='entregado' AND p.fecha >= '2026-01-01'
                 GROUP BY 1,2""").pivot(index="region", columns="mes", values="dias").reset_index()
    c = _q(d, """SELECT c.region, COUNT(*) resenas_2026 FROM resenas r JOIN pedidos p USING(pedido_id)
                 JOIN clientes c USING(cliente_id) WHERE p.fecha >= '2026-01-01' GROUP BY 1""")
    return ("Puntaje promedio de reseñas por región y mes (2026):\n" + md(a, "{:.2f}")
            + "\n\nDías promedio de entrega por región y mes (2026):\n" + md(b, "{:.1f}")
            + "\n\nCantidad de reseñas por región (2026):\n" + md(c))


def ctx_app(d):
    a = _q(d, f"""SELECT p.canal, COUNT(DISTINCT p.pedido_id) pedidos, COUNT(DISTINCT p.cliente_id) clientes,
                 {FACT}/COUNT(DISTINCT p.pedido_id)/1e3 ticket_promedio_miles,
                 {FACT}/COUNT(DISTINCT p.cliente_id)/1e3 facturacion_por_cliente_miles
                 FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado'
                 AND p.fecha BETWEEN '2026-01-01' AND '2026-06-30' AND p.cliente_id<>999999 GROUP BY 1""")
    a["pedidos_por_cliente"] = a["pedidos"] / a["clientes"]
    b = _q(d, f"""SELECT p.canal, pr.categoria, {FACT}/1e6 f FROM pedidos p JOIN items i USING(pedido_id)
                 JOIN productos pr USING(producto_id) WHERE p.estado='entregado'
                 AND p.fecha BETWEEN '2026-01-01' AND '2026-06-30' AND p.cliente_id<>999999 GROUP BY 1,2""")
    b = b.pivot(index="categoria", columns="canal", values="f")
    b = (b / b.sum() * 100).round(1).reset_index()
    b.columns = ["categoria", "% de la facturación app", "% de la facturación web"]
    c = _q(d, """SELECT substr(fecha,1,4)||'-S'||CASE WHEN CAST(substr(fecha,6,2) AS INT)<=6 THEN '1' ELSE '2' END periodo,
                 ROUND(AVG(canal='app')*100,1) pct_pedidos_app FROM pedidos GROUP BY 1""")
    return ("Pedidos entregados de enero a junio 2026 por canal (pesos corrientes; 'clientes' = clientes distintos "
            "que compraron por ese canal):\n" + md(a)
            + "\n\nMix de categorías por canal (enero a junio 2026):\n" + md(b)
            + "\n\nParticipación de la app en los pedidos:\n" + md(c))


def ctx_cupon(d):
    a = _q(d, f"""SELECT substr(p.fecha,1,7) mes, COUNT(DISTINCT p.pedido_id) pedidos_entregados,
                 {FACT}/1e6 facturacion_M, SUM(CASE WHEN p.cupon IS NOT NULL THEN 1 ELSE 0 END) lineas_con_cupon
                 FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado'
                 AND p.fecha BETWEEN '2025-06-01' AND '2025-10-31' GROUP BY 1""")
    a = a.drop(columns=["lineas_con_cupon"])
    nuevos = _q(d, """SELECT substr(primera,1,7) mes, COUNT(*) clientes_nuevos FROM
                   (SELECT cliente_id, MIN(fecha) primera FROM pedidos WHERE estado='entregado' GROUP BY 1)
                   WHERE primera BETWEEN '2025-06-01' AND '2025-10-31' GROUP BY 1""")
    a = a.merge(nuevos, on="mes")
    cup = _q(d, f"""WITH f AS (SELECT cliente_id, MIN(fecha) primera FROM pedidos WHERE estado='entregado' GROUP BY 1)
                   SELECT COUNT(DISTINCT p.pedido_id) pedidos_con_cupon,
                   SUM(CASE WHEN p.fecha > f.primera THEN 1.0 ELSE 0 END)/COUNT(*)*100 pct_lineas_clientes_que_ya_habian_comprado,
                   {FACT}/0.9*0.1/1e6 descuento_otorgado_M
                   FROM pedidos p JOIN items i USING(pedido_id) JOIN f USING(cliente_id)
                   WHERE p.cupon='VUELTA10' AND p.estado='entregado'""")
    return ("Campaña de cupón VUELTA10 (10% de descuento, vigente del 1 al 31 de agosto de 2025).\n\n"
            "Pedidos entregados por mes (pesos corrientes):\n" + md(a)
            + "\n\nUso del cupón en agosto:\n" + md(cup))


def ctx_ab(d):
    a = _q(d, """SELECT variante, COUNT(*) usuarios, SUM(convirtio) conversiones,
                 ROUND(AVG(convirtio)*100,2) conversion_pct FROM sesiones_ab GROUP BY 1""")
    b = _q(d, """SELECT CASE WHEN fecha<='2026-05-10' THEN '1-10 may' WHEN fecha<='2026-05-20' THEN '11-20 may'
                 ELSE '21-31 may' END periodo, variante, ROUND(AVG(convirtio)*100,2) conv FROM sesiones_ab
                 GROUP BY 1,2""").pivot(index="periodo", columns="variante", values="conv").reset_index()
    b.columns = ["periodo", "conversion_A_pct", "conversion_B_pct"]
    return ("Experimento de checkout, mayo 2026. A = checkout actual, B = checkout nuevo de un solo paso. "
            "Asignación aleatoria 50/50 por usuario. Test de diferencia de proporciones de dos colas: p-valor = "
            f"{_p_ab(d):.4f}.\n\n" + md(a, "{:.2f}") + "\n\nConversión por período:\n" + md(b, "{:.2f}"))


def _p_ab(d):
    import numpy as np
    from scipy import stats
    a = _q(d, "SELECT variante, SUM(convirtio) x, COUNT(*) n FROM sesiones_ab GROUP BY 1").set_index("variante")
    pa, pb = a.x["A"] / a.n["A"], a.x["B"] / a.n["B"]
    pp = a.x.sum() / a.n.sum()
    z = (pb - pa) / np.sqrt(pp * (1 - pp) * (1 / a.n["A"] + 1 / a.n["B"]))
    return float(2 * stats.norm.sf(abs(z)))


def ctx_ticket(d):
    t = _q(d, f"""SELECT substr(p.fecha,1,7) mes, p.pedido_id, p.cliente_id, {FACT} ticket FROM pedidos p
                 JOIN items i USING(pedido_id) WHERE p.estado='entregado' AND p.fecha BETWEEN '2026-02-01'
                 AND '2026-06-30' GROUP BY 1,2,3""")
    a = t.groupby("mes")["ticket"].agg(pedidos="count", ticket_promedio="mean", ticket_mediano="median").reset_index()
    top = t[t.mes == "2026-05"].sort_values("ticket", ascending=False).head(8)[["pedido_id", "cliente_id", "ticket"]]
    return ("Dashboard comercial, pedidos entregados (pesos corrientes):\n" + md(a, "{:,.0f}")
            + "\n\nLos 8 pedidos con ticket más alto de mayo 2026:\n" + md(top, "{:,.0f}"))


def ctx_priorizar(d):
    nova = _q(d, """SELECT substr(p.fecha,1,7) mes, SUM(i.cantidad) unidades, SUM(i.cantidad*i.precio_unitario)/1e6 f
                    FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado' AND i.producto_id=1
                    AND p.fecha BETWEEN '2026-01-01' AND '2026-04-30' GROUP BY 1""")
    nova.columns = ["mes", "unidades Celular Nova X", "facturación Celular Nova X (M ARS)"]
    pat = _q(d, """SELECT CASE WHEN p.fecha<'2026-04-01' THEN 'ene-mar 2026' ELSE 'abr-jun 2026' END periodo,
                   ROUND(AVG(r.puntaje),2) puntaje_patagonia, COUNT(DISTINCT p.cliente_id) clientes_con_resena
                   FROM resenas r JOIN pedidos p USING(pedido_id) JOIN clientes c USING(cliente_id)
                   WHERE c.region='Patagonia' AND p.fecha>='2026-01-01' GROUP BY 1""")
    pfac = _q(d, f"""SELECT {FACT}/1e6 f FROM pedidos p JOIN items i USING(pedido_id) JOIN clientes c USING(cliente_id)
                    WHERE c.region='Patagonia' AND p.estado='entregado' AND p.fecha BETWEEN '2026-01-01' AND '2026-06-30'""")
    tot = _q(d, f"""SELECT {FACT}/1e6 f, COUNT(DISTINCT p.pedido_id) n FROM pedidos p JOIN items i USING(pedido_id)
                   WHERE p.estado='entregado' AND p.fecha BETWEEN '2026-01-01' AND '2026-06-30' AND p.cliente_id<>999999""")
    return ("Tenés capacidad para encarar UNA sola iniciativa este trimestre. Datos disponibles:\n\n"
            "1) Quiebres de stock: el Celular Nova X estuvo sin stock del 3 al 28 de marzo de 2026.\n" + md(nova)
            + "\n\n2) Logística Patagonia: en abril se cambió de operador logístico en Patagonia.\n" + md(pat)
            + f"\nFacturación de Patagonia ene-jun 2026: {pfac.f[0]:,.1f} M ARS.\n\n"
            + _ab_line(d) +
            "Implementarlo para todos lleva 6 semanas de desarrollo.\n\n"
            f"Totales de la empresa ene-jun 2026: facturación {tot.f[0]:,.1f} M ARS, {tot.n[0]:,} pedidos entregados. "
            "Se estima que el 100% de las ventas pasa por el checkout.")


def _ab_line(d):
    a = _q(d, "SELECT variante, AVG(convirtio)*100 c FROM sesiones_ab GROUP BY 1").set_index("variante")["c"]
    return (f"3) Checkout nuevo: el test A/B de mayo dio conversión {a['A']:.2f}% (A) contra {a['B']:.2f}% (B), "
            f"p-valor = {_p_ab(d):.3f}. ").replace(".", ",")


def ctx_activos(d):
    a = _q(d, """WITH u AS (SELECT cliente_id, MAX(fecha) ultima FROM pedidos WHERE estado='entregado' GROUP BY 1)
                 SELECT CASE WHEN ultima >= '2026-06-01' THEN 'a) último pedido en jun-2026'
                             WHEN ultima >= '2026-04-01' THEN 'b) último pedido en abr-may 2026'
                             WHEN ultima >= '2026-01-01' THEN 'c) último pedido en ene-mar 2026'
                             WHEN ultima >= '2025-07-01' THEN 'd) último pedido en jul-dic 2025'
                             ELSE 'e) último pedido en ene-jun 2025' END tramo, COUNT(*) clientes
                 FROM u GROUP BY 1 ORDER BY 1""")
    b = _q(d, "SELECT COUNT(*) n FROM clientes")
    c = _q(d, "SELECT cliente_id, nombre, email, segmento FROM clientes WHERE segmento='interno'")
    return ("Hoy es 1 de julio de 2026. La tabla clientes tiene " f"{b.n[0]:,} registros.\n\n"
            "Clientes con al menos un pedido entregado, según la fecha de su último pedido entregado:\n" + md(a)
            + "\n\nRegistros de la tabla clientes con segmento 'interno':\n" + md(c))


def ctx_abril(d):
    a = _q(d, """SELECT fecha, COUNT(*) pedidos, SUM(canal='app') app, SUM(canal='web') web FROM pedidos
                 WHERE fecha BETWEEN '2026-04-06' AND '2026-04-21' GROUP BY fecha""")
    full = _q(d, "SELECT fecha FROM pedidos WHERE fecha BETWEEN '2026-04-06' AND '2026-04-21' GROUP BY fecha")
    import pandas as pd
    dias = pd.DataFrame({"fecha": pd.date_range("2026-04-06", "2026-04-21").strftime("%Y-%m-%d")})
    a = dias.merge(a, on="fecha", how="left").fillna(0)
    for c in ("pedidos", "app", "web"):
        a[c] = a[c].astype(int)
    _ = full
    return ("Reporte diario de pedidos (todos los estados), abril 2026:\n" + md(a)
            + "\n\nEl 14 de abril de 2026 fue martes y no fue feriado.")


def ctx_resumen(d):
    rows = []
    for nombre, a, b in [("H1 2025", "2025-01-01", "2025-06-30"), ("H1 2026", "2026-01-01", "2026-06-30")]:
        k = _q(d, f"""SELECT {FACT}/1e6 fact, COUNT(DISTINCT p.pedido_id) ped, COUNT(DISTINCT p.cliente_id) cli
                     FROM pedidos p JOIN items i USING(pedido_id) WHERE p.estado='entregado' AND p.fecha BETWEEN ? AND ?
                     AND p.cliente_id<>999999""", (a, b))
        c = _q(d, "SELECT AVG(estado='cancelado')*100 canc, AVG(canal='app')*100 app FROM pedidos WHERE fecha BETWEEN ? AND ?",
               (a, b))
        r = _q(d, """SELECT AVG(r.puntaje) p FROM resenas r JOIN pedidos p USING(pedido_id) WHERE p.fecha BETWEEN ? AND ?""",
               (a, b))
        rows.append(dict(periodo=nombre, facturacion_M_ARS=k.fact[0], pedidos_entregados=int(k.ped[0]),
                         clientes_activos=int(k.cli[0]), ticket_promedio_miles=k.fact[0] * 1e3 / k.ped[0],
                         pct_cancelacion=c.canc[0], pct_pedidos_app=c.app[0], puntaje_resenas=r.p[0]))
    import pandas as pd
    t = pd.DataFrame(rows)
    return ("KPIs del primer semestre (excluye pedidos de prueba de QA). Montos en pesos corrientes. "
            "Los precios de lista de la empresa subieron en promedio 2,2% por mes en el período (≈30% interanual).\n\n"
            + md(t, "{:,.2f}") + "\n\nHechos del semestre: quiebre de stock del Celular Nova X (3 al 28 de marzo); "
            "corte del procesador de tarjetas (10 al 16 de marzo); cambio de operador logístico en Patagonia "
            "(abril); test A/B de checkout con resultado positivo (mayo); Hot Sale (11 al 13 de mayo).")


INSIGHT_TASKS = [
    _txt("I01", "¿Por qué cayó marzo?",
         "El gerente comercial te escribe: 'Las ventas cayeron en marzo, ¿qué pasó?'. Respondele en máximo 8 líneas.",
         ctx_marzo,
         ["La caída se concentra en Tecnología: el Celular Nova X casi no vendió en marzo (quiebre de stock) y "
          "parte de la demanda se pasó al Nova Lite",
          "Del 10 al 16 de marzo la aprobación de tarjetas cayó a ~45% (vs ~95%) y subieron los cancelados",
          "La baja de Electro es estacional (fin del verano, también pasó en 2025), no es un problema nuevo",
          "Cuantifica el impacto con los números de las tablas",
          "Propone una acción (alertas de stock, contingencia con el procesador de pagos)"],
         "Marzo cayó ~12% contra febrero. La mayor parte es Tecnología: el Celular Nova X pasó de ~X unidades a casi "
         "cero (quiebre de stock), y solo una parte se pasó al Nova Lite. Además, del 10 al 16 de marzo la aprobación "
         "de tarjetas bajó a ~45%, lo que disparó los cancelados. Electro baja todos los años en marzo (fin del verano). "
         "Propuesta: alertas de stock para los top sellers y un procesador de respaldo."),
    _txt("I02", "Reseñas en Patagonia",
         "Atención al cliente avisa que 'en Patagonia los clientes están cada vez más enojados'. ¿Es cierto? "
         "¿Qué lo explica? Respondé en máximo 8 líneas.",
         ctx_patagonia,
         ["Confirma con datos: el puntaje de Patagonia cae fuerte desde abril 2026 (de ~3,9 a ~3,0); las otras "
          "regiones están estables",
          "Coincide con un salto de ~4-5 días en los tiempos de entrega de Patagonia desde abril",
          "Distingue correlación de causa: sugiere revisar qué cambió en abril (operador logístico, rutas)",
          "Propone acción concreta y cómo medir si se corrige"],
         "Sí: Patagonia pasó de ~3,9 a ~3,0 desde abril mientras las demás regiones siguen igual. En el mismo mes los "
         "días de entrega de Patagonia subieron de ~7,5 a ~12. Revisaría qué cambió en la logística en abril."),
    _txt("I03", "¿La app es un problema?",
         "El director financiero dice: 'La app trae pedidos más baratos; nos está bajando el ticket. Habría que dejar "
         "de empujarla'. ¿Estás de acuerdo? Respondé en máximo 8 líneas.",
         ctx_app,
         ["Reconoce que el ticket de la app es menor",
          "Muestra que los clientes de la app compran más seguido (más pedidos por cliente), así que la métrica "
          "relevante es facturación por cliente, no ticket",
          "Explica que el mix de categorías es distinto (más Moda/Belleza, menos Electro): no es la misma compra",
          "No concluye más de lo que los datos permiten (ej. faltan márgenes y costos de adquisición) y propone "
          "qué mirar"],
         "El ticket de la app es más bajo, pero sus clientes compran más seguido; hay que mirar facturación por "
         "cliente y margen por categoría, no ticket. El mix es distinto (más Moda y Belleza). No dejaría de empujarla "
         "sin ver margen y costo de adquisición."),
    _txt("I04", "¿Funcionó el cupón?",
         "Marketing dice que la campaña VUELTA10 de agosto 2025 'fue un éxito porque crecieron los pedidos'. "
         "¿Qué opinás? Respondé en máximo 8 líneas.",
         ctx_cupon,
         ["Agosto tuvo más pedidos que julio y septiembre (incremento real pero moderado)",
          "La enorme mayoría de los usos fue de clientes que ya habían comprado: poca adquisición, mucha "
          "canibalización (habrían comprado igual, pero con descuento)",
          "Los clientes nuevos no subieron de forma notable",
          "Compara el descuento otorgado con la facturación incremental",
          "Recomienda cómo medirlo mejor (grupo de control / holdout)"],
         "Agosto creció ~X% en pedidos, pero ~9 de cada 10 usos del cupón fueron de clientes existentes y los clientes "
         "nuevos no subieron: gran parte del descuento fue a gente que iba a comprar igual. Hay que comparar descuento "
         "vs facturación incremental y la próxima vez usar un grupo de control."),
    _txt("I05", "Recomendación del A/B",
         "Escribile al Product Manager tu recomendación sobre el experimento de checkout, en máximo 6 líneas.",
         ctx_ab,
         ["B convierte ~4,2% vs ~3,7% de A: ~0,45 puntos, ~12% relativo",
          "La diferencia es estadísticamente significativa (p < 0,05) y consistente en los tres períodos",
          "Recomienda implementar B (o un rollout gradual) monitoreando la conversión",
          "No sobrevende: menciona incertidumbre del tamaño del efecto o qué seguir midiendo"],
         "Recomiendo implementar B: convierte 4,20% vs 3,74% (+12% relativo), significativo (p<0,05) y estable en las "
         "tres decenas del mes. Haría un rollout gradual y seguiría la conversión dos semanas."),
    _txt("I06", "El ticket récord de mayo",
         "El CEO vio en el dashboard que el ticket promedio de mayo subió mucho y quiere anunciarlo en la reunión "
         "general. ¿Qué le decís? Máximo 6 líneas.",
         ctx_ticket,
         ["El ticket promedio está inflado por pedidos de prueba de QA (9.999.999, cliente 999999) cargados en "
          "producción",
          "La mediana casi no se movió, lo que confirma que es un efecto de outliers",
          "Recomienda no anunciarlo, excluir los pedidos de prueba y corregir el dashboard (y su origen)"],
         "No lo anunciaría: el promedio está inflado por 15 pedidos de prueba de QA de $9.999.999 del cliente 999999. "
         "La mediana subió apenas ~2%. Hay que excluirlos y arreglar el dashboard."),
    _txt("I07", "Priorizar",
         "Tenés que recomendar en qué iniciativa enfocar al equipo este trimestre. Elegí una, justificá con números "
         "y explicá por qué no las otras. Máximo 10 líneas.",
         ctx_priorizar,
         ["Estima el impacto de cada opción en pesos o en porcentaje usando los datos",
          "Checkout: +0,46 pp sobre 3,74% ≈ +12% de conversión sobre el 100% de las ventas es probablemente el "
          "mayor impacto recurrente",
          "Stock: el quiebre costó del orden de cientos de millones en un mes, pero es evitable con alertas "
          "baratas (no requiere todo el trimestre)",
          "Patagonia: problema serio de experiencia pero sobre una porción chica de la facturación",
          "Explicita supuestos e incertidumbre; la recomendación es coherente con sus propios números"],
         "Elijo el checkout: +12% de conversión sobre el 100% de las ventas (~X M ARS por semestre) supera las otras "
         "opciones. El quiebre de stock costó ~Y M ARS en marzo, pero se resuelve con alertas sin frenar al equipo. "
         "Patagonia es ~11% de la facturación; lo escalaría con el operador logístico."),
    _txt("I08", "¿Cuántos clientes activos?",
         "El directorio pregunta: '¿Cuántos clientes activos tenemos?'. Respondé en máximo 6 líneas.",
         ctx_activos,
         ["Señala que 'activo' necesita una definición (ventana de tiempo) y no responde un número sin aclararla",
          "Da números para al menos dos definiciones (ej. compró en los últimos 90 días / últimos 12 meses), "
          "sumando correctamente los tramos de la tabla",
          "No usa el total de la tabla clientes como 'activos'",
          "Excluye o menciona el registro interno de QA"],
         "Depende de la ventana: con compra en los últimos 90 días (abr-jun) son X; en los últimos 12 meses, Y. "
         "No usaría los 7.001 registros de la tabla (incluyen un usuario interno de QA). Propongo fijar 90 días."),
    _txt("I09", "El día raro",
         "Tu jefe te pide el informe semanal y ve el reporte diario de abril. ¿Qué le decís sobre lo que se ve? "
         "Máximo 6 líneas.",
         ctx_abril,
         ["Detecta que el 14 de abril tiene 0 pedidos en todos los canales",
          "Lo interpreta como probable falla de datos (pipeline/carga), no como caída real de ventas: el día "
          "anterior y el siguiente son normales y no fue feriado",
          "Recomienda verificar con la fuente/ingeniería antes de reportar y marcarlo o reprocesar",
          "No extrapola ni inventa una causa de negocio"],
         "El 14 de abril aparece con cero pedidos en web y app, con días normales antes y después y sin feriado: "
         "casi seguro es una falla de carga, no de ventas. Lo verificaría con ingeniería y reprocesaría antes de "
         "publicar el informe."),
    _txt("I10", "Resumen para el directorio",
         "Escribí el resumen ejecutivo del primer semestre 2026 para el directorio: 5 bullets, cada uno con un número.",
         ctx_resumen,
         ["Usa los números correctos de la tabla y no inventa otros",
          "Señala que el crecimiento de facturación es nominal: con precios +~30% interanual, el crecimiento real "
          "es mucho menor (o lo ajusta)",
          "Usa pedidos o clientes como medida de volumen real",
          "Menciona los hechos relevantes (marzo, Patagonia, A/B) con su efecto",
          "Prioriza: lo más importante primero, accionable"],
         "Facturación +X% nominal, pero con precios +30% el crecimiento real es ~Y%; pedidos +Z%. Marzo perdió ventas "
         "por quiebre de stock y corte de tarjetas. Patagonia empeoró en reseñas desde abril. Checkout B: +12% de "
         "conversión, a implementar."),
]

TASKS = SQL_TASKS + CLEAN_TASKS + VIZ_TASKS + STATS_TASKS + INSIGHT_TASKS
BY_ID = {t["id"]: t for t in TASKS}
BLOQUES = ["SQL", "Limpieza", "Visualización", "Estadística", "Insight de negocio"]


def file_preview(data_dir, name, n=4):
    path = os.path.join(data_dir, name)
    enc = "latin-1" if name == "ventas_sucursales.csv" else "utf-8"
    with open(path, "rb") as f:
        raw = f.read(4000).decode(enc, errors="replace")
    lines = raw.splitlines()[:n]
    return f"Primeras {n} líneas de {name}:\n```\n" + "\n".join(lines) + "\n```"


def build_prompt(task, data_dir):
    if task["kind"] in ("sql", "viz"):
        return task["prompt"]
    if task["kind"] == "python":
        prev = "\n\n".join(file_preview(data_dir, f) for f in task.get("files", []))
        return f"{SCHEMA}\n\n{prev}\n\nTarea: {task['enunciado']}\n\n{PY_RULES}".replace("\n\n\n", "\n\n")
    ctx = task["contexto_fn"](data_dir)
    return (f"Sos analista de datos en Tienda Pampa, un e-commerce argentino.\n\nDatos:\n{ctx}\n\n"
            f"Pedido: {task['enunciado']}\n\n{TEXT_RULES}")


SYSTEM = ("Sos un analista de datos junior en tu primera semana en Tienda Pampa, un e-commerce argentino. "
          "Respondé en español y seguí exactamente el formato que se te pide.")
