"""Corre la función solve() de una respuesta en un proceso separado e imprime el resultado como JSON."""
import importlib.util
import json
import math
import sys

MARK = "__BENCH_RESULT__"


def to_jsonable(x):
    try:
        import numpy as np
        import pandas as pd
    except ImportError:  # pragma: no cover
        np = pd = None
    if pd is not None:
        if isinstance(x, pd.DataFrame):
            return [to_jsonable(r) for r in x.itertuples(index=False)]
        if isinstance(x, pd.Series):
            return {to_key(k): to_jsonable(v) for k, v in x.items()}
        if isinstance(x, (pd.Timestamp, pd.Period)):
            return str(x)
    if np is not None:
        if isinstance(x, np.bool_):
            return bool(x)
        if isinstance(x, np.integer):
            return int(x)
        if isinstance(x, np.floating):
            return float(x)
        if isinstance(x, np.ndarray):
            return [to_jsonable(v) for v in x.tolist()]
    if isinstance(x, dict):
        return {to_key(k): to_jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [to_jsonable(v) for v in x]
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return str(x)


def to_key(k):
    k = to_jsonable(k)
    if isinstance(k, float) and k.is_integer():
        k = int(k)
    return str(k)


def main():
    sol, data_dir, mode, out_png = sys.argv[1:5]
    spec = importlib.util.spec_from_file_location("solution", sol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "solve"):
        raise SystemExit("no se encontró una función solve()")
    if mode == "viz":
        mod.solve(data_dir, out_png)
        return
    res = mod.solve(data_dir)
    sys.stdout.write("\n" + MARK + json.dumps(to_jsonable(res), ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
