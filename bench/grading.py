"""Ejecución de respuestas y corrección automática."""
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unicodedata

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_runner.py")
MARK = "__BENCH_RESULT__"


# ------------------------------------------------------------------ extracción
def strip_thinking(text):
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def extract_code(text, lang):
    text = strip_thinking(text)
    blocks = re.findall(r"```([a-zA-Z0-9_+-]*)[ \t]*\n(.*?)```", text, flags=re.S)
    if not blocks:
        return None
    same = [b for l, b in blocks if l.lower() == lang]
    chosen = same[-1] if same else blocks[-1][1]
    return chosen.strip()


# ------------------------------------------------------------------ ejecución
def run_sql(db_path, sql, timeout=20, max_rows=20000):
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    t0 = time.time()
    con.set_progress_handler(lambda: 1 if time.time() - t0 > timeout else 0, 10000)
    try:
        cur = con.execute(sql)
        rows = cur.fetchmany(max_rows + 1)
        if len(rows) > max_rows:
            raise RuntimeError(f"la consulta devolvió más de {max_rows} filas")
        return [list(r) for r in rows]
    finally:
        con.close()


def run_python(code, data_dir, mode="value", timeout=120):
    """Ejecuta `solve` en un subproceso aislado, sobre una COPIA de los datos.

    mode="value": devuelve el resultado de solve(data_dir).
    mode="viz": llama solve(data_dir, out_path) y devuelve el PNG generado (bytes).
    """
    work = tempfile.mkdtemp(prefix="bench_")
    try:
        ddir = os.path.join(work, "data")
        shutil.copytree(data_dir, ddir)
        sol = os.path.join(work, "solution.py")
        with open(sol, "w", encoding="utf-8") as f:
            f.write(code)
        out_png = os.path.join(work, "out.png")
        mpl_cache = os.path.join(tempfile.gettempdir(), "analista_bench_mplcache")
        os.makedirs(mpl_cache, exist_ok=True)
        env = dict(os.environ, MPLBACKEND="Agg", PYTHONHASHSEED="0", MPLCONFIGDIR=mpl_cache)
        p = subprocess.run([sys.executable, "-I", RUNNER, sol, ddir, mode, out_png], cwd=work, env=env,
                           capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            raise RuntimeError(_tail(p.stderr) or "el código terminó con error")
        if mode == "viz":
            if not os.path.exists(out_png) or os.path.getsize(out_png) < 1000:
                raise RuntimeError("el código corrió pero no guardó un PNG en out_path")
            with open(out_png, "rb") as f:
                return f.read()
        line = [l for l in p.stdout.splitlines() if l.startswith(MARK)]
        if not line:
            raise RuntimeError("solve() no devolvió un resultado serializable")
        return json.loads(line[-1][len(MARK):])
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"timeout: el código tardó más de {timeout}s")
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _tail(s, n=6):
    lines = [l for l in (s or "").strip().splitlines() if l.strip()]
    return "\n".join(lines[-n:])


# ------------------------------------------------------------------ comparación
def norm_key(k):
    s = unicodedata.normalize("NFKD", str(k)).encode("ascii", "ignore").decode()
    return " ".join(s.lower().strip().split())


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def num_close(a, b, tol=0.01, rel=1e-6):
    if not (_is_num(a) and _is_num(b)):
        return False
    if math.isnan(a) or math.isnan(b):
        return False
    return abs(a - b) <= max(tol, rel * max(abs(a), abs(b)))


def compare(exp, got, spec, path="resultado"):
    t = spec["type"]
    if t in ("number", "int"):
        if t == "int" and not (_is_num(got) and float(got).is_integer()):
            return False, f"{path}: esperaba un entero, recibió {got!r}"
        tol = spec.get("tol", 0 if t == "int" else 0.01)
        rel = spec.get("rel", 0 if t == "int" else 1e-6)
        if num_close(float(exp), got, tol, rel):
            return True, ""
        return False, f"{path}: esperado {exp!r}, recibido {got!r}"
    if t == "bool":
        if isinstance(got, bool) and got == exp:
            return True, ""
        return False, f"{path}: esperado {exp!r}, recibido {got!r}"
    if t == "str":
        if isinstance(got, str) and norm_key(got) == norm_key(exp):
            return True, ""
        return False, f"{path}: esperado {exp!r}, recibido {got!r}"
    if t == "list":
        if not isinstance(got, list) or len(got) != len(exp):
            return False, f"{path}: esperaba una lista de {len(exp)} elementos, recibió {got!r}"
        for i, (e, g) in enumerate(zip(exp, got)):
            ok, msg = compare(e, g, spec["items"], f"{path}[{i}]")
            if not ok:
                return ok, msg
        return True, ""
    if t == "dict":
        if not isinstance(got, dict):
            return False, f"{path}: esperaba un dict, recibió {type(got).__name__}"
        ge = {norm_key(k): v for k, v in exp.items()}
        gg = {norm_key(k): v for k, v in got.items()}
        if set(ge) != set(gg):
            falt = sorted(set(ge) - set(gg))
            sob = sorted(set(gg) - set(ge))
            return False, f"{path}: claves distintas. Faltan {falt[:6]}; sobran {sob[:6]}"
        fields = {norm_key(k): v for k, v in spec.get("fields", {}).items()}
        for k in ge:
            ok, msg = compare(ge[k], gg[k], fields.get(k, spec.get("values")), f"{path}[{k!r}]")
            if not ok:
                return ok, msg
        return True, ""
    if t == "table":
        return compare_table(exp, got, spec)
    raise ValueError(t)


def _cell_eq(e, g, tol):
    if _is_num(e) and _is_num(g):
        return num_close(float(e), float(g), tol, 1e-9)
    if e is None or g is None:
        return e is None and g is None
    return norm_key(e) == norm_key(g)


def _sort_key(row):
    return tuple(("%.2f" % c) if _is_num(c) else norm_key(c) for c in row)


def compare_table(exp, got, spec):
    tol = spec.get("tol", 0.01)
    if len(exp) != len(got):
        return False, f"esperaba {len(exp)} filas, recibió {len(got)}"
    if exp and len(exp[0]) != len(got[0]):
        return False, f"esperaba {len(exp[0])} columnas, recibió {len(got[0])}"
    e, g = exp, got
    if not spec.get("ordered", True):
        e, g = sorted(exp, key=_sort_key), sorted(got, key=_sort_key)
    for i, (re_, rg) in enumerate(zip(e, g)):
        for j, (ce, cg) in enumerate(zip(re_, rg)):
            if not _cell_eq(ce, cg, tol):
                return False, f"fila {i + 1}, columna {j + 1}: esperado {ce!r}, recibido {cg!r}"
    return True, ""


# ------------------------------------------------------------------ alto nivel
def expected_value(task, data_dir):
    if task["kind"] == "sql":
        return run_sql(os.path.join(data_dir, "tienda.db"), task["ref"])
    return run_python(task["ref"], data_dir)


def grade_auto(task, response_text, data_dir, expected):
    lang = "sql" if task["kind"] == "sql" else "python"
    code = extract_code(response_text, lang)
    if code is None:
        return dict(ok=False, error="no encontré un bloque de código en la respuesta", code=None)
    try:
        if task["kind"] == "sql":
            got = run_sql(os.path.join(data_dir, "tienda.db"), code)
        else:
            got = run_python(code, data_dir)
    except Exception as ex:  # noqa: BLE001
        return dict(ok=False, error=f"error al ejecutar: {ex}", code=code)
    ok, msg = compare(expected, got, task["check"])
    return dict(ok=ok, error=msg, code=code, got=_short(got))


def grade_viz(task, response_text, data_dir, png_path):
    code = extract_code(response_text, "python")
    if code is None:
        return dict(ok=False, error="no encontré un bloque de código en la respuesta", code=None)
    try:
        png = run_python(code, data_dir, mode="viz")
    except Exception as ex:  # noqa: BLE001
        return dict(ok=False, error=f"error al ejecutar: {ex}", code=code)
    with open(png_path, "wb") as f:
        f.write(png)
    return dict(ok=True, error="", code=code, png=os.path.basename(png_path))


def _short(x, n=600):
    s = json.dumps(x, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[:n] + "…"
