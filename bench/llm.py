"""Clientes mínimos (solo librería estándar) para Ollama y APIs compatibles con OpenAI."""
import json
import os
import time
import urllib.error
import urllib.request


class LLMError(RuntimeError):
    pass


class LLMTimeout(LLMError):
    """El modelo no respondió a tiempo: cuenta como tarea fallida, no como error de infraestructura."""


def _is_timeout(e):
    import socket
    if isinstance(e, (socket.timeout, TimeoutError)):
        return True
    reason = getattr(e, "reason", None)
    return isinstance(reason, (socket.timeout, TimeoutError))


def _post(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "User-Agent": "analista-junior-bench/1.0", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def chat(model_cfg, system, user, max_retries=6):
    """Devuelve dict(text, thinking_chars, usage, latency_s)."""
    prov = model_cfg["provider"]
    timeout = model_cfg.get("timeout_s", 900)
    for attempt in range(max_retries):
        t0 = time.time()
        try:
            if prov == "ollama":
                base = model_cfg.get("base_url", "http://localhost:11434")
                payload = {"model": model_cfg["model"], "stream": False,
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                           "options": {"temperature": model_cfg.get("temperature", 0),
                                       "num_ctx": model_cfg.get("num_ctx", 16384), "seed": 0,
                                       # tope de tokens: evita que un modelo chico quede razonando en bucle
                                       "num_predict": model_cfg.get("num_predict", 8192)}}
                if "think" in model_cfg:
                    payload["think"] = model_cfg["think"]
                r = _post(base.rstrip("/") + "/api/chat", payload, {}, timeout)
                msg = r.get("message", {})
                return dict(text=msg.get("content", ""), thinking_chars=len(msg.get("thinking") or ""),
                            usage={"prompt_tokens": r.get("prompt_eval_count"),
                                   "completion_tokens": r.get("eval_count")},
                            latency_s=round(time.time() - t0, 2), finish_reason=r.get("done_reason"))
            if prov == "openai_compat":
                key = os.environ.get(model_cfg["api_key_env"], "")
                if not key:
                    raise LLMError(f"falta la variable de entorno {model_cfg['api_key_env']}")
                payload = {"model": model_cfg["model"], "temperature": model_cfg.get("temperature", 0),
                           "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
                payload["max_tokens"] = model_cfg.get("max_tokens", 16000)
                payload.update(model_cfg.get("extra_body", {}))
                r = _post(model_cfg["base_url"].rstrip("/") + "/chat/completions", payload,
                          {"Authorization": f"Bearer {key}"}, timeout)
                ch = r["choices"][0]["message"]
                return dict(text=ch.get("content") or "", thinking_chars=len(ch.get("reasoning") or ""),
                            usage=r.get("usage", {}), latency_s=round(time.time() - t0, 2),
                            finish_reason=r["choices"][0].get("finish_reason"))
            raise LLMError(f"provider desconocido: {prov}")
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                wait = float(e.headers.get("retry-after") or 0) or min(120, 10 * 2 ** attempt)
                print(f"    HTTP {e.code}, reintento en {wait:.0f}s…", flush=True)
                time.sleep(wait)
                continue
            raise LLMError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if _is_timeout(e):
                raise LLMTimeout(f"el modelo no terminó de responder en {timeout}s")
            if attempt < max_retries - 1:
                time.sleep(10)
                continue
            raise LLMError(f"no pude conectar con el modelo: {e}")
    raise LLMError("se agotaron los reintentos")
