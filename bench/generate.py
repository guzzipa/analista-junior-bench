"""Genera el dataset sintético de "Tienda Pampa", un e-commerce argentino ficticio.

Todo es determinístico (semilla fija), así cualquiera que corra el benchmark
obtiene exactamente los mismos datos. Los datos tienen patrones "plantados"
a propósito (una caída de ventas en marzo 2026, un corte de pagos, pedidos de
prueba, un día sin datos, etc.) para que las tareas tengan respuestas
verificables.
"""
import csv
import datetime as dt
import os
import sqlite3

import numpy as np

SEED = 42
START = dt.date(2025, 1, 1)
END = dt.date(2026, 6, 30)

REGIONES = {
    "AMBA": (["CABA", "Buenos Aires"], 0.45, (2, 3)),
    "Centro": (["Córdoba", "Santa Fe", "Entre Ríos"], 0.20, (3, 5)),
    "Cuyo": (["Mendoza", "San Juan", "San Luis"], 0.08, (4, 6)),
    "NOA": (["Tucumán", "Salta", "Jujuy"], 0.09, (5, 7)),
    "NEA": (["Corrientes", "Misiones", "Chaco"], 0.07, (5, 8)),
    "Patagonia": (["Neuquén", "Río Negro", "Chubut"], 0.11, (6, 9)),
}

# (nombre, categoria, precio enero 2025 en ARS, popularidad)
PRODUCTOS = [
    ("Celular Nova X", "Tecnología", 520000, 9.0),
    ("Celular Nova Lite", "Tecnología", 310000, 3.0),
    ("Notebook Andes 14", "Tecnología", 890000, 2.0),
    ("Auriculares Bluetooth Pulse", "Tecnología", 45000, 5.0),
    ("Smartwatch Ritmo", "Tecnología", 150000, 2.5),
    ("Tablet Lago 10", "Tecnología", 380000, 1.5),
    ("Cargador Rápido 30W", "Tecnología", 18000, 4.0),
    ("Aire Acondicionado Split 3000", "Electro", 780000, 4.0),
    ("Heladera No Frost 360L", "Electro", 1150000, 1.5),
    ("Lavarropas Carga Frontal 8kg", "Electro", 820000, 1.5),
    ("Smart TV 55 4K", "Electro", 690000, 2.5),
    ("Microondas Digital 25L", "Electro", 190000, 2.0),
    ("Ventilador de Pie Turbo", "Electro", 85000, 3.0),
    ("Cafetera Express Barista", "Electro", 240000, 1.5),
    ("Juego de Sábanas Algodón", "Hogar", 42000, 3.0),
    ("Set de Ollas Antiadherentes", "Hogar", 98000, 2.5),
    ("Silla de Escritorio Ergo", "Hogar", 210000, 1.5),
    ("Lámpara LED de Pie", "Hogar", 36000, 2.0),
    ("Organizador de Placard", "Hogar", 27000, 2.0),
    ("Colchón Espuma 2 Plazas", "Hogar", 450000, 1.0),
    ("Zapatillas Running Viento", "Deportes", 125000, 4.0),
    ("Bicicleta Rodado 29", "Deportes", 620000, 1.0),
    ("Mancuernas 10kg Par", "Deportes", 55000, 2.0),
    ("Colchoneta Yoga", "Deportes", 19000, 2.5),
    ("Botella Térmica 1L", "Deportes", 28000, 3.0),
    ("Remera Dry Fit", "Moda", 22000, 5.0),
    ("Jean Clásico", "Moda", 48000, 4.0),
    ("Campera Inflable", "Moda", 135000, 2.0),
    ("Mochila Urbana", "Moda", 52000, 3.0),
    ("Zapatillas Urbanas Clásicas", "Moda", 98000, 3.0),
    ("Perfume Brisa 100ml", "Belleza", 68000, 3.0),
    ("Crema Facial Hidratante", "Belleza", 21000, 4.0),
    ("Secador de Pelo Pro", "Belleza", 75000, 2.0),
    ("Protector Solar FPS50", "Belleza", 16000, 4.0),
    ("Shampoo Sólido Natural", "Belleza", 9000, 3.5),
]

CAT_MIX_WEB = {"Tecnología": 0.27, "Electro": 0.22, "Hogar": 0.15, "Deportes": 0.12, "Moda": 0.13, "Belleza": 0.11}
CAT_MIX_APP = {"Tecnología": 0.20, "Electro": 0.10, "Hogar": 0.13, "Deportes": 0.12, "Moda": 0.25, "Belleza": 0.20}

SEASON = {1: 0.94, 2: 0.95, 3: 0.98, 4: 0.97, 5: 1.05, 6: 1.00, 7: 1.05, 8: 1.00, 9: 0.97, 10: 1.02, 11: 1.15, 12: 1.45}
HOT_SALE = {dt.date(2025, 5, 12), dt.date(2025, 5, 13), dt.date(2025, 5, 14),
            dt.date(2026, 5, 11), dt.date(2026, 5, 12), dt.date(2026, 5, 13)}
CYBER = {dt.date(2025, 11, 3), dt.date(2025, 11, 4), dt.date(2025, 11, 5)}
STOCKOUT = (dt.date(2026, 3, 3), dt.date(2026, 3, 28))       # sin stock de Celular Nova X
OUTAGE = (dt.date(2026, 3, 10), dt.date(2026, 3, 16))        # corte del procesador de tarjetas
DIA_SIN_DATOS = dt.date(2026, 4, 14)                         # falla del pipeline
CUPON = ("VUELTA10", dt.date(2025, 8, 1), dt.date(2025, 8, 31))
PATAGONIA_NUEVO_CORREO = dt.date(2026, 4, 1)
TEST_CLIENTE_ID = 999999
TEST_PRODUCTO_ID = 999

NOMBRES = ["Sofía", "Mateo", "Valentina", "Benjamín", "Martina", "Joaquín", "Lucía", "Tomás",
           "Catalina", "Santiago", "Emilia", "Felipe", "Julieta", "Lautaro", "Camila", "Thiago",
           "Agustina", "Facundo", "Florencia", "Nicolás", "Paula", "Ignacio", "Micaela", "Franco"]
APELLIDOS = ["González", "Rodríguez", "Gómez", "Fernández", "López", "Díaz", "Martínez", "Pérez",
             "García", "Sánchez", "Romero", "Sosa", "Álvarez", "Torres", "Ruiz", "Ramírez",
             "Flores", "Acosta", "Benítez", "Medina", "Herrera", "Suárez", "Aguirre", "Giménez"]


def months_since_start(d):
    return (d.year - START.year) * 12 + d.month - START.month


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=1)


def build(data_dir):
    rng = np.random.default_rng(SEED)
    os.makedirs(data_dir, exist_ok=True)
    db_path = os.path.join(data_dir, "tienda.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    # ---------------- productos ----------------
    productos = []
    for i, (nombre, cat, precio, pop) in enumerate(PRODUCTOS, start=1):
        costo_ratio = {"Tecnología": 0.78, "Electro": 0.80, "Hogar": 0.62, "Deportes": 0.60,
                       "Moda": 0.50, "Belleza": 0.45}[cat]
        productos.append(dict(producto_id=i, nombre=nombre, categoria=cat, precio_lista=precio,
                              costo=round(precio * costo_ratio), pop=pop))
    prod_by_cat = {}
    for p in productos:
        prod_by_cat.setdefault(p["categoria"], []).append(p)
    NOVA_X, NOVA_LITE, AIRE = 1, 2, 8

    # ---------------- clientes ----------------
    n_clientes = 7000
    reg_names = list(REGIONES)
    reg_w = np.array([REGIONES[r][1] for r in reg_names])
    clientes = []
    alta_start = dt.date(2024, 6, 1)
    span = (END - alta_start).days
    # altas más concentradas al principio (base histórica) y luego un flujo constante
    offs = np.sort(np.concatenate([rng.integers(0, 214, 2600), rng.integers(0, span, n_clientes - 2600)]))
    for cid in range(1, n_clientes + 1):
        region = reg_names[rng.choice(len(reg_names), p=reg_w)]
        prov = REGIONES[region][0][rng.integers(len(REGIONES[region][0]))]
        alta = alta_start + dt.timedelta(days=int(offs[cid - 1]))
        prog = (alta - alta_start).days / span
        p_app = 0.12 + 0.62 * prog
        canal_pref = "app" if rng.random() < p_app else "web"
        nombre = f"{NOMBRES[rng.integers(len(NOMBRES))]} {APELLIDOS[rng.integers(len(APELLIDOS))]}"
        email = (nombre.lower().replace(" ", ".").translate(str.maketrans("áéíóúñ", "aeioun"))
                 + f"{cid}@mail.com")
        segmento = rng.choice(["particular", "particular", "particular", "pyme"])
        clientes.append(dict(cliente_id=cid, nombre=nombre, email=email, provincia=prov, region=region,
                             fecha_alta=alta, segmento=str(segmento), canal_pref=canal_pref,
                             peso=(1.7 if canal_pref == "app" else 1.0) * rng.lognormal(0, 0.6)))
    altas = np.array([(c["fecha_alta"] - START).days for c in clientes])
    pesos = np.array([c["peso"] for c in clientes])

    # ---------------- pedidos ----------------
    pedidos, items, pagos, resenas = [], [], [], []
    pid = 100000
    for d in daterange(START, END):
        m = months_since_start(d)
        lam = 52 * (1.012 ** m) * SEASON[d.month] * (0.85 if d.weekday() >= 5 else 1.05)
        if d in HOT_SALE:
            lam *= 3.2
        if d in CYBER:
            lam *= 2.4
        if CUPON[1] <= d <= CUPON[2]:
            lam *= 1.12
        if d.month == 12 and d.day <= 23:
            lam *= 1.1
        n = rng.poisson(lam)
        elig = np.searchsorted(altas, (d - START).days, side="right")
        if elig == 0:
            continue
        w = pesos[:elig] / pesos[:elig].sum()
        idx = rng.choice(elig, size=n, p=w)
        price_idx = 1.022 ** m
        for ci in idx:
            c = clientes[ci]
            canal = c["canal_pref"] if rng.random() < 0.85 else ("web" if c["canal_pref"] == "app" else "app")
            mix = CAT_MIX_APP if canal == "app" else CAT_MIX_WEB
            cats = list(mix)
            cw = np.array([mix[k] for k in cats])
            n_items = 1 + rng.poisson(0.55)
            lineas = {}
            for _ in range(n_items):
                cat = cats[rng.choice(len(cats), p=cw / cw.sum())]
                plist = prod_by_cat[cat]
                pw = np.array([p["pop"] for p in plist], dtype=float)
                if cat == "Electro":
                    summer = d.month in (12, 1, 2)
                    pw = np.array([p["pop"] * (3.0 if (summer and p["producto_id"] == AIRE) else
                                               (0.3 if p["producto_id"] == AIRE else 1.0)) for p in plist])
                prod = plist[rng.choice(len(plist), p=pw / pw.sum())]
                p_id = prod["producto_id"]
                if p_id == NOVA_X and STOCKOUT[0] <= d <= STOCKOUT[1]:
                    if rng.random() < 0.7:
                        continue
                    p_id = NOVA_LITE
                    prod = productos[NOVA_LITE - 1]
                cant = int(1 + rng.poisson(0.8)) if prod["categoria"] == "Belleza" else (
                    int(1 + rng.poisson(0.15)) if prod["categoria"] in ("Moda", "Deportes") else 1)
                precio = prod["precio_lista"] * price_idx * rng.uniform(0.97, 1.03)
                if d in HOT_SALE or d in CYBER:
                    precio *= 0.85
                lineas[p_id] = (lineas.get(p_id, (0, precio))[0] + cant, precio)
            if not lineas:
                continue
            cupon = None
            if CUPON[1] <= d <= CUPON[2] and rng.random() < 0.30:
                cupon = CUPON[0]
            pid += 1
            total = 0.0
            for p_id, (cant, precio) in lineas.items():
                if cupon:
                    precio *= 0.90
                precio = round(precio / 10) * 10
                items.append((pid, p_id, cant, float(precio)))
                total += cant * precio
            # pago
            medio = rng.choice(["tarjeta", "transferencia", "billetera"], p=[0.60, 0.25, 0.15])
            cuotas = int(rng.choice([1, 3, 6, 12], p=[0.35, 0.30, 0.20, 0.15])) if medio == "tarjeta" else 1
            if medio == "tarjeta":
                p_ok = 0.50 if OUTAGE[0] <= d <= OUTAGE[1] else 0.95
            else:
                p_ok = 0.99
            ok = rng.random() < p_ok
            pagos.append((pid, str(medio), cuotas, round(total, 2), int(ok), d.isoformat()))
            pagado = ok
            if not ok and rng.random() < 0.35:
                pagos.append((pid, "transferencia", 1, round(total, 2), 1, d.isoformat()))
                pagado = True
            if not pagado:
                estado = "cancelado"
            elif rng.random() < 0.05:
                estado = "cancelado"
            else:
                cats_ped = {productos[p - 1]["categoria"] for p in lineas}
                p_dev = 0.09 if "Moda" in cats_ped else 0.03
                estado = "devuelto" if rng.random() < p_dev else "entregado"
            fecha_entrega = None
            if estado != "cancelado":
                lo, hi = REGIONES[c["region"]][2]
                dias = int(rng.integers(lo, hi + 1))
                if c["region"] == "Patagonia" and d >= PATAGONIA_NUEVO_CORREO:
                    dias += int(rng.integers(3, 7))
                if d.month == 12 and d.day >= 15:
                    dias += 1
                fecha_entrega = (d + dt.timedelta(days=dias)).isoformat()
                if estado == "entregado" and rng.random() < 0.40:
                    score = 4.75 - 0.22 * max(0, dias - 4) + rng.normal(0, 0.7)
                    puntaje = int(min(5, max(1, round(score))))
                    coment = None
                    if rng.random() < 0.3:
                        coment = ("Llegó tarde" if dias > 7 else ("Excelente" if puntaje >= 4 else "Regular"))
                    resenas.append((pid, puntaje, coment))
            pedidos.append((pid, c["cliente_id"], d.isoformat(), estado, canal, cupon, fecha_entrega))

    # día sin datos (falla de pipeline): se borran todos los registros de ese día
    perdidos = {p[0] for p in pedidos if p[2] == DIA_SIN_DATOS.isoformat()}
    pedidos = [p for p in pedidos if p[0] not in perdidos]
    items = [x for x in items if x[0] not in perdidos]
    pagos = [x for x in pagos if x[0] not in perdidos]
    resenas = [x for x in resenas if x[0] not in perdidos]

    # pedidos de prueba de QA cargados en producción (mayo 2026)
    test_days = sorted(rng.choice(np.arange(1, 29), size=20, replace=True))
    for k, day in enumerate(test_days):
        pid += 1
        d = dt.date(2026, 5, int(day))
        monto = 9999999.0 if k < 15 else 0.0
        pedidos.append((pid, TEST_CLIENTE_ID, d.isoformat(), "entregado", "web", None, d.isoformat()))
        items.append((pid, TEST_PRODUCTO_ID, 1, monto))
        pagos.append((pid, "tarjeta", 1, monto, 1, d.isoformat()))

    # ---------------- experimento A/B (checkout) ----------------
    ab = []
    n_ab = 42000
    for u in range(1, n_ab + 1):
        var = "A" if u % 2 else "B"
        p = 0.038 if var == "A" else 0.0435
        f = dt.date(2026, 5, 1) + dt.timedelta(days=int(rng.integers(0, 31)))
        ab.append((u, var, int(rng.random() < p), f.isoformat()))

    # ---------------- escribir SQLite ----------------
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE clientes (cliente_id INTEGER PRIMARY KEY, nombre TEXT, email TEXT, provincia TEXT,
                           region TEXT, fecha_alta TEXT, segmento TEXT);
    CREATE TABLE productos (producto_id INTEGER PRIMARY KEY, nombre TEXT, categoria TEXT,
                            precio_lista REAL, costo REAL);
    CREATE TABLE pedidos (pedido_id INTEGER PRIMARY KEY, cliente_id INTEGER, fecha TEXT, estado TEXT,
                          canal TEXT, cupon TEXT, fecha_entrega TEXT);
    CREATE TABLE items (pedido_id INTEGER, producto_id INTEGER, cantidad INTEGER, precio_unitario REAL);
    CREATE TABLE pagos (pedido_id INTEGER, medio TEXT, cuotas INTEGER, monto REAL, aprobado INTEGER, fecha TEXT);
    CREATE TABLE resenas (pedido_id INTEGER, puntaje INTEGER, comentario TEXT);
    CREATE TABLE sesiones_ab (usuario_id INTEGER, variante TEXT, convirtio INTEGER, fecha TEXT);
    """)
    cur.executemany("INSERT INTO clientes VALUES (?,?,?,?,?,?,?)",
                    [(c["cliente_id"], c["nombre"], c["email"], c["provincia"], c["region"],
                      c["fecha_alta"].isoformat(), c["segmento"]) for c in clientes]
                    + [(TEST_CLIENTE_ID, "QA TEST", "qa@tiendapampa.test", "CABA", "AMBA", "2026-05-01", "interno")])
    cur.executemany("INSERT INTO productos VALUES (?,?,?,?,?)",
                    [(p["producto_id"], p["nombre"], p["categoria"], p["precio_lista"], p["costo"]) for p in productos]
                    + [(TEST_PRODUCTO_ID, "PRODUCTO TEST", "Tecnología", 9999999, 0)])
    cur.executemany("INSERT INTO pedidos VALUES (?,?,?,?,?,?,?)", pedidos)
    cur.executemany("INSERT INTO items VALUES (?,?,?,?)", items)
    cur.executemany("INSERT INTO pagos VALUES (?,?,?,?,?,?)", pagos)
    cur.executemany("INSERT INTO resenas VALUES (?,?,?)", resenas)
    cur.executemany("INSERT INTO sesiones_ab VALUES (?,?,?,?)", ab)
    con.commit()
    con.close()

    _raw_files(data_dir, clientes, productos, items, rng)


# ---------------------------------------------------------------- archivos "sucios"
PROV_VARIANTES = {
    "CABA": ["CABA", "Capital Federal", "C.A.B.A.", "caba", "Ciudad de Buenos Aires"],
    "Buenos Aires": ["Buenos Aires", "Bs As", "BUENOS AIRES", "Pcia. de Buenos Aires", "bs. as."],
    "Córdoba": ["Córdoba", "Cordoba", "CÓRDOBA", "Cba"],
    "Santa Fe": ["Santa Fe", "Sta Fe", "SANTA FE"],
    "Entre Ríos": ["Entre Ríos", "Entre Rios", "E. Rios"],
    "Mendoza": ["Mendoza", "MENDOZA", "Mza"],
    "San Juan": ["San Juan", "SAN JUAN"],
    "San Luis": ["San Luis", "san luis"],
    "Tucumán": ["Tucumán", "Tucuman", "TUCUMAN"],
    "Salta": ["Salta", "SALTA"],
    "Jujuy": ["Jujuy", "JUJUY"],
    "Corrientes": ["Corrientes", "Ctes"],
    "Misiones": ["Misiones", "MISIONES"],
    "Chaco": ["Chaco", "Chaco "],
    "Neuquén": ["Neuquén", "Neuquen", "NQN"],
    "Río Negro": ["Río Negro", "Rio Negro", "R. Negro"],
    "Chubut": ["Chubut", "CHUBUT"],
}


def _ar_number(x, decimals=2):
    s = f"{x:,.{decimals}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _raw_files(data_dir, clientes, productos, items, rng):
    # --- clientes_crm.csv: export de CRM con duplicados, formatos mezclados y nulos
    rows = []
    base = [clientes[i] for i in sorted(rng.choice(len(clientes), size=3000, replace=False))]
    for c in base:
        rows.append(c)
    dups = rng.choice(len(base), size=240, replace=False)
    for i in dups:
        rows.append(dict(base[i], _dup=True))
    order = rng.permutation(len(rows))
    with open(os.path.join(data_dir, "clientes_crm.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["id_crm", "nombre", "email", "provincia", "fecha_alta", "telefono", "monto_compras"])
        for k, oi in enumerate(order, start=1):
            c = rows[oi]
            email = c["email"]
            if c.get("_dup"):
                email = rng.choice([email.upper(), " " + email, email + " ", email.capitalize()])
            elif rng.random() < 0.05:
                email = email.upper()
            prov = rng.choice(PROV_VARIANTES[c["provincia"]])
            fa = c["fecha_alta"]
            fmt = rng.integers(3)
            if fmt == 0:
                fstr = fa.isoformat()
            elif fmt == 1:
                fstr = fa.strftime("%d/%m/%Y")
            else:
                fstr = f"{fa.day}-{fa.month}-{fa.strftime('%y')}"
            r = rng.random()
            if r < 0.04:
                tel = ""
            elif r < 0.07:
                tel = "NA"
            elif r < 0.10:
                tel = "-"
            elif r < 0.12:
                tel = "sin dato"
            else:
                tel = f"11{rng.integers(10000000, 99999999)}"
            monto = float(round(rng.lognormal(11.5, 1.0), 2))
            mf = rng.integers(3)
            if monto < 1000 and mf == 2:
                mstr = str(int(round(monto)))
                monto = float(int(round(monto)))
            elif mf == 1:
                mstr = "$ " + _ar_number(monto)
            else:
                mstr = _ar_number(monto)
            wr.writerow([f"CRM{k:05d}", "  " + c["nombre"].upper() + " " if rng.random() < 0.1 else c["nombre"],
                         email, prov, fstr, tel, mstr])

    # --- ventas_sucursales.csv: export de Excel argentino (latin-1, ;, coma decimal)
    sucursales = ["Córdoba Centro", "San Martín", "Rosario Norte", "Mendoza Güemes", "Tucumán Plaza", "Neuquén Este"]
    with open(os.path.join(data_dir, "ventas_sucursales.csv"), "w", newline="", encoding="latin-1") as f:
        wr = csv.writer(f, delimiter=";")
        wr.writerow(["fecha", "sucursal", "venta"])
        for d in daterange(dt.date(2026, 1, 1), dt.date(2026, 3, 31)):
            for s_i, s in enumerate(sucursales):
                v = rng.lognormal(14.2 + 0.15 * s_i, 0.25)
                wr.writerow([d.strftime("%d/%m/%Y"), s, _ar_number(v)])

    # --- items_raw.csv: códigos de producto con formatos inconsistentes
    sample = [items[i] for i in rng.choice(len(items) - 20, size=2000, replace=False)]
    with open(os.path.join(data_dir, "items_raw.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["pedido_id", "producto", "cantidad", "precio_unitario"])
        for (p, prod, cant, precio) in sample:
            fmt = rng.integers(4)
            code = [f"P-{prod:04d}", f"p{prod}", f" {prod} ", f"P{prod:04d}"][fmt]
            wr.writerow([p, code, cant, precio])

    # --- eventos.csv: timestamps en UTC
    with open(os.path.join(data_dir, "eventos.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["timestamp_utc", "evento"])
        base_ts = dt.datetime(2026, 6, 1, 3, 0, 0)  # 00:00 hora Argentina
        for _ in range(6000):
            # más actividad a la noche argentina (que en UTC ya es el día siguiente)
            day = int(rng.integers(0, 7))
            hour_local = float(rng.choice(np.arange(24), p=_hour_weights()))
            ts = base_ts + dt.timedelta(days=day, hours=hour_local, seconds=int(rng.integers(0, 3600)))
            ev = rng.choice(["login", "busqueda", "agregar_carrito", "compra"], p=[0.3, 0.4, 0.2, 0.1])
            wr.writerow([ts.strftime("%Y-%m-%dT%H:%M:%SZ"), ev])

    # --- ventas_wide.csv: una columna por mes, montos con $ y separador de miles
    cats = ["Tecnología", "Electro", "Hogar", "Deportes", "Moda", "Belleza"]
    meses = [f"2025-{m:02d}" for m in range(1, 13)]
    with open(os.path.join(data_dir, "ventas_wide.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["categoria"] + meses)
        for ci, cat in enumerate(cats):
            vals = []
            for mi in range(12):
                base_v = (40 - ci * 5) * 1e6 * (1.022 ** mi) * SEASON[mi + 1]
                if cat == "Electro" and mi in (0, 1):
                    base_v *= 1.9  # pico de aires en verano
                vals.append("$ " + _ar_number(base_v * rng.uniform(0.95, 1.05), 0))
            wr.writerow([cat] + vals)

    # --- devoluciones_envio.csv: datos con paradoja de Simpson
    filas = []
    spec = [("Moto", "AMBA", 800, 32), ("Moto", "Interior", 200, 20),
            ("Correo", "AMBA", 200, 6), ("Correo", "Interior", 800, 72)]
    for metodo, seg, n, dev in spec:
        flags = [1] * dev + [0] * (n - dev)
        for fl in flags:
            filas.append((metodo, seg, fl))
    perm = rng.permutation(len(filas))
    with open(os.path.join(data_dir, "devoluciones_envio.csv"), "w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["envio_id", "metodo", "segmento", "devuelto"])
        for k, i in enumerate(perm, start=1):
            wr.writerow([k, *filas[i]])


def _hour_weights():
    w = np.array([2, 1, 1, 0.5, 0.5, 0.5, 1, 2, 3, 4, 5, 5, 5, 5, 5, 5, 5, 6, 7, 8, 9, 9, 7, 4], dtype=float)
    return w / w.sum()


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "data")
    print("ok")
