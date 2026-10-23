"""Línea de comandos del benchmark: setup, run, review, report, verify."""
import argparse
import json
import os
import random
import subprocess
import sys
import time

from . import generate, grading, llm
from .tasks import BLOQUES, BY_ID, SYSTEM, TASKS, build_prompt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RESULTS = os.path.join(ROOT, "results")
EXPECTED = os.path.join(DATA, "expected.json")
SCORES = os.path.join(RESULTS, "puntajes_humanos.json")

# Criterio de "aprobó el período de prueba". Fijado ANTES de correr cualquier modelo.
APRUEBA_TOTAL = 0.70
APRUEBA_MIN_BLOQUE = 0.50


# ------------------------------------------------------------------ helpers
def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def load_models():
    return load_json(os.path.join(ROOT, "models.json"), {})["models"]


def ensure_data():
    if not os.path.exists(os.path.join(DATA, "tienda.db")):
        print("Generando datos…")
        generate.build(DATA)
    exp = load_json(EXPECTED, None)
    if exp is None:
        print("Calculando respuestas correctas con las soluciones de referencia…")
        exp = {}
        for t in TASKS:
            if t["kind"] in ("sql", "python"):
                exp[t["id"]] = grading.expected_value(t, DATA)
        save_json(EXPECTED, exp)
    return exp


def select_tasks(arg):
    if not arg:
        return TASKS
    ids = [x.strip().upper() for x in arg.split(",")]
    out = []
    for i in ids:
        if i in BY_ID:
            out.append(BY_ID[i])
        else:
            out += [t for t in TASKS if t["id"].startswith(i)]
    return out


def reference_answer(task):
    lang = {"sql": "sql", "python": "python", "viz": "python"}.get(task["kind"])
    if lang:
        return f"```{lang}\n{task['ref']}\n```"
    return task["ref"]


# ------------------------------------------------------------------ comandos
def cmd_setup(args):
    ensure_data()
    print(f"Listo. Datos en {DATA}")


def cmd_list(args):
    for t in TASKS:
        print(f"{t['id']}  {t['bloque']:<20} {t['titulo']}")
    print("\nModelos configurados:")
    for m in load_models():
        print(f"  {m['name']:<22} {m['provider']:<14} {m['model']}")


def run_one(task, model_cfg, expected, out_dir, call):
    rec_path = os.path.join(out_dir, f"{task['id']}.json")
    prompt = build_prompt(task, DATA)
    try:
        resp = call(task, prompt)
    except llm.LLMError as ex:
        print(f"  {task['id']}: ERROR del modelo: {ex}")
        return None
    rec = dict(task_id=task["id"], bloque=task["bloque"], model=model_cfg["name"], response=resp["text"],
               thinking_chars=resp.get("thinking_chars", 0), usage=resp.get("usage", {}),
               latency_s=resp.get("latency_s"), timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))
    if task["kind"] in ("sql", "python"):
        rec["grade"] = grading.grade_auto(task, resp["text"], DATA, expected[task["id"]])
        estado = "OK " if rec["grade"]["ok"] else "MAL"
    elif task["kind"] == "viz":
        rec["grade"] = grading.grade_viz(task, resp["text"], DATA, os.path.join(out_dir, f"{task['id']}.png"))
        estado = "PNG" if rec["grade"]["ok"] else "MAL"
    else:
        rec["grade"] = {"ok": None}
        estado = "TXT"
    save_json(rec_path, rec)
    detalle = "" if rec["grade"].get("ok") in (True, None) else "  " + rec["grade"]["error"].splitlines()[0][:110]
    print(f"  {task['id']} [{estado}] {resp.get('latency_s', 0):6.1f}s{detalle}", flush=True)
    return rec


def cmd_run(args):
    expected = ensure_data()
    models = {m["name"]: m for m in load_models()}
    if args.model not in models:
        sys.exit(f"Modelo '{args.model}' no está en models.json. Opciones: {', '.join(models)}")
    cfg = models[args.model]
    out_dir = os.path.join(RESULTS, cfg["name"])
    os.makedirs(out_dir, exist_ok=True)
    tasks = select_tasks(args.tasks)
    print(f"Corriendo {len(tasks)} tareas con {cfg['name']} ({cfg['model']})")
    pause = cfg.get("min_interval_s", 0)

    def call(task, prompt):
        return llm.chat(cfg, SYSTEM, prompt)

    for t in tasks:
        if os.path.exists(os.path.join(out_dir, f"{t['id']}.json")) and not args.force:
            continue
        run_one(t, cfg, expected, out_dir, call)
        if pause:
            time.sleep(pause)
    print("Terminado. Siguiente paso: python bench.py review  (y después python bench.py report)")


def cmd_regrade(args):
    """Vuelve a corregir respuestas guardadas (útil si cambiás datos o tolerancias)."""
    expected = ensure_data()
    for name in sorted(os.listdir(RESULTS)) if os.path.isdir(RESULTS) else []:
        d = os.path.join(RESULTS, name)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            rec = load_json(os.path.join(d, f), None)
            t = BY_ID.get(rec["task_id"])
            if t and t["kind"] in ("sql", "python"):
                rec["grade"] = grading.grade_auto(t, rec["response"], DATA, expected[t["id"]])
                save_json(os.path.join(d, f), rec)
    print("Recorrección terminada.")


def cmd_verify(args):
    """Chequea el harness: las soluciones de referencia sacan 100% y respuestas malas fallan."""
    expected = ensure_data()
    fails = 0
    for t in TASKS:
        if t["kind"] in ("sql", "python"):
            g = grading.grade_auto(t, reference_answer(t), DATA, expected[t["id"]])
            bad = "```sql\nSELECT 1\n```" if t["kind"] == "sql" else "```python\ndef solve(data_dir):\n    return 0\n```"
            gb = grading.grade_auto(t, bad, DATA, expected[t["id"]])
            ok = g["ok"] and not gb["ok"]
            print(f"  {t['id']} referencia={'OK' if g['ok'] else 'FALLA'} respuesta_mala={'rechazada' if not gb['ok'] else 'ACEPTADA'}"
                  + ("" if g["ok"] else f"  {g['error'][:200]}"))
        elif t["kind"] == "viz":
            tmp = os.path.join(RESULTS, "_verify", f"{t['id']}.png")
            os.makedirs(os.path.dirname(tmp), exist_ok=True)
            g = grading.grade_viz(t, reference_answer(t), DATA, tmp)
            ok = g["ok"]
            print(f"  {t['id']} referencia={'PNG OK' if ok else 'FALLA ' + g['error'][:200]}")
        else:
            try:
                build_prompt(t, DATA)
                ok = True
            except Exception as ex:  # noqa: BLE001
                ok = False
                print(f"  {t['id']} contexto FALLA: {ex}")
            else:
                print(f"  {t['id']} contexto OK")
        fails += 0 if ok else 1
    print("\nTodo OK." if fails == 0 else f"\n{fails} problemas.")
    return fails


def _open_file(path):
    opener = "open" if sys.platform == "darwin" else "xdg-open"
    try:
        subprocess.Popen([opener, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        print(f"  (abrí a mano: {path})")


def cmd_review(args):
    """Corrección humana a ciegas de gráficos e insights."""
    scores = load_json(SCORES, {})
    pend = []
    for name in sorted(os.listdir(RESULTS)) if os.path.isdir(RESULTS) else []:
        d = os.path.join(RESULTS, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        for f in sorted(os.listdir(d)):
            if not f.endswith(".json"):
                continue
            rec = load_json(os.path.join(d, f), None)
            t = BY_ID.get(rec["task_id"])
            if not t or t["kind"] not in ("viz", "text"):
                continue
            if t["kind"] == "viz" and not rec["grade"].get("ok"):
                continue  # no corrió: vale 0, no hace falta revisarlo
            if rec["task_id"] in scores.get(name, {}):
                continue
            pend.append((name, t, rec))
    if not pend:
        print("No hay nada pendiente de corrección humana.")
        return
    random.Random(args.seed).shuffle(pend)
    print(f"{len(pend)} respuestas para corregir. El modelo está oculto para que la corrección sea a ciegas.")
    print("Puntaje 1 a 5. 's' = saltear, 'q' = salir (se guarda lo hecho).\n")
    for k, (name, t, rec) in enumerate(pend, start=1):
        print("=" * 90)
        print(f"[{k}/{len(pend)}] {t['id']} · {t['bloque']} · {t['titulo']}")
        print("-" * 90)
        print(t.get("enunciado") or t["prompt"].split("Tarea: ")[-1].split("\n\n")[0])
        print("\nQué buscar:")
        for p in t["puntos_clave"]:
            print(f"  • {p}")
        print("\nEscala:\n" + t["rubric"])
        print("-" * 90)
        if t["kind"] == "viz":
            png = os.path.join(RESULTS, name, rec["grade"]["png"])
            print("Se abrió el gráfico en otra ventana.")
            _open_file(png)
        else:
            print(grading.strip_thinking(rec["response"]))
        print("-" * 90)
        while True:
            s = input("Puntaje (1-5, s, q): ").strip().lower()
            if s in ("1", "2", "3", "4", "5"):
                scores.setdefault(name, {})[t["id"]] = int(s)
                save_json(SCORES, scores)
                break
            if s == "s":
                break
            if s == "q":
                print("Guardado. Podés seguir después con python bench.py review")
                return
    print("\nCorrección humana terminada. Ahora: python bench.py report")


def collect():
    scores = load_json(SCORES, {})
    rows = {}
    for name in sorted(os.listdir(RESULTS)) if os.path.isdir(RESULTS) else []:
        d = os.path.join(RESULTS, name)
        if not os.path.isdir(d) or name.startswith("_"):
            continue
        recs = {}
        for f in os.listdir(d):
            if f.endswith(".json"):
                rec = load_json(os.path.join(d, f), None)
                recs[rec["task_id"]] = rec
        if recs:
            rows[name] = (recs, scores.get(name, {}))
    return rows


def task_score(t, rec, human):
    """Devuelve puntaje 0..1, o None si falta la corrección humana."""
    if rec is None:
        return None
    if t["kind"] in ("sql", "python"):
        return 1.0 if rec["grade"]["ok"] else 0.0
    if t["kind"] == "viz" and not rec["grade"].get("ok"):
        return 0.0
    s = human.get(t["id"])
    return None if s is None else (s - 1) / 4


def cmd_report(args):
    data = collect()
    if not data:
        sys.exit("Todavía no hay resultados. Corré primero: python bench.py run --model <nombre>")
    lines = ["# Resultados: analista junior vs. IA gratis", "",
             f"Criterio de aprobación (fijado antes de correr): total ≥ {APRUEBA_TOTAL:.0%} y ningún bloque "
             f"por debajo de {APRUEBA_MIN_BLOQUE:.0%}.", ""]
    header = "| Modelo | " + " | ".join(BLOQUES) + " | Total | ¿Aprobó? | Tiempo total | Costo |"
    lines += [header, "|" + "---|" * (len(BLOQUES) + 5)]
    summary = []
    pending_total = 0
    for name, (recs, human) in data.items():
        bloques = {}
        pend = 0
        for b in BLOQUES:
            vals = []
            for t in [t for t in TASKS if t["bloque"] == b]:
                s = task_score(t, recs.get(t["id"]), human)
                if s is None:
                    pend += 1
                else:
                    vals.append(s)
            n_b = len([t for t in TASKS if t["bloque"] == b])
            bloques[b] = sum(vals) / n_b if len(vals) == n_b else None
        pending_total += pend
        complete = all(v is not None for v in bloques.values())
        total = sum(bloques.values()) / len(BLOQUES) if complete else None
        aprobo = (total is not None and total >= APRUEBA_TOTAL and min(bloques.values()) >= APRUEBA_MIN_BLOQUE)
        secs = sum((r.get("latency_s") or 0) for r in recs.values())
        fmt = lambda v: "pendiente" if v is None else f"{v:.0%}"  # noqa: E731
        veredicto = "pendiente" if total is None else ("SÍ" if aprobo else "NO")
        lines.append(f"| {name} | " + " | ".join(fmt(bloques[b]) for b in BLOQUES)
                     + f" | {fmt(total)} | {veredicto} | {secs / 60:.0f} min | USD 0 |")
        summary.append(dict(modelo=name, total=total, aprobo=aprobo if total is not None else None,
                            minutos=round(secs / 60, 1), tareas_respondidas=len(recs), pendientes_humanos=pend,
                            **{b: bloques[b] for b in BLOQUES}))
    if pending_total:
        lines += ["", f"Faltan {pending_total} correcciones humanas (o tareas sin correr). "
                      "Corré `python bench.py review` para completarlas."]
    # fallos automáticos, materia prima para el contenido
    lines += ["", "## Fallos de las tareas autocorregidas", ""]
    for name, (recs, _) in data.items():
        fl = [(tid, r) for tid, r in sorted(recs.items()) if r["grade"].get("ok") is False]
        lines.append(f"### {name} ({len(fl)} fallos)")
        for tid, r in fl:
            msg = (r["grade"].get("error") or "").replace("\n", " ")[:220]
            lines.append(f"- **{tid} {BY_ID[tid]['titulo']}**: {msg}")
        lines.append("")
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, "reporte.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    import csv
    with open(os.path.join(RESULTS, "resumen.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    _chart(summary)
    print("\n".join(lines[:len(data) + 6]))
    print(f"\nReporte completo: {os.path.join(RESULTS, 'reporte.md')}")
    print(f"Gráfico: {os.path.join(RESULTS, 'grafico_resultados.png')}")


def _chart(summary):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    names = [s["modelo"] for s in summary]
    fig, ax = plt.subplots(figsize=(11, 0.9 + 0.75 * len(names) * 1.0 + 2))
    h = 0.8 / len(BLOQUES)
    colors = ["#1f6f8b", "#99a8b2", "#e6a400", "#2e8b57", "#c0392b"]
    y = np.arange(len(names))
    for k, b in enumerate(BLOQUES):
        vals = [(s[b] or 0) * 100 for s in summary]
        ax.barh(y + k * h, vals, height=h, label=b, color=colors[k])
    ax.axvline(APRUEBA_TOTAL * 100, color="k", ls="--", lw=1)
    ax.text(APRUEBA_TOTAL * 100 + 1, len(names) - 0.2, "70% para aprobar", fontsize=9)
    ax.set_yticks(y + 0.4 - h / 2)
    def etiqueta(s):
        tot = "pendiente" if s["total"] is None else "{:.0%}".format(s["total"])
        return "{}\n(total {})".format(s["modelo"], tot)
    ax.set_yticklabels([etiqueta(s) for s in summary])
    ax.set_xlim(0, 100); ax.set_xlabel("% de puntaje por bloque")
    ax.set_title("50 tareas de analista junior, 5 IAs gratis")
    ax.legend(loc="lower right", fontsize=8)
    ax.invert_yaxis()
    fig.savefig(os.path.join(RESULTS, "grafico_resultados.png"), dpi=150, bbox_inches="tight")


def main():
    ap = argparse.ArgumentParser(prog="bench.py", description="Analista junior vs. IA gratis")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("setup", help="genera los datos y las respuestas correctas")
    sub.add_parser("list", help="lista tareas y modelos")
    r = sub.add_parser("run", help="corre las tareas con un modelo")
    r.add_argument("--model", required=True)
    r.add_argument("--tasks", help="ej. S01,S02 o un prefijo como S o L0")
    r.add_argument("--force", action="store_true", help="vuelve a correr tareas ya respondidas")
    sub.add_parser("regrade", help="recorrige respuestas guardadas")
    rv = sub.add_parser("review", help="corrección humana a ciegas de gráficos e insights")
    rv.add_argument("--seed", type=int, default=7)
    sub.add_parser("report", help="arma la tabla de resultados y el gráfico")
    sub.add_parser("verify", help="chequea que el harness funcione")
    args = ap.parse_args()
    fn = {"setup": cmd_setup, "list": cmd_list, "run": cmd_run, "regrade": cmd_regrade, "review": cmd_review,
          "report": cmd_report, "verify": cmd_verify}[args.cmd]
    res = fn(args)
    if args.cmd == "verify" and res:
        sys.exit(1)
