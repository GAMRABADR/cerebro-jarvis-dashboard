"""Cascata AI multi-provider. Chiavi solo da os.environ — mai loggate."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

# Alias Agente-0 usr.env → nomi canonici usati dalla cascata.
_ALIASES = {
    "API_KEY_GROQ": "GROQ_API_KEY",
    "API_KEY_GEMINI": "GEMINI_API_KEY",
    "API_KEY_GOOGLE": "GOOGLE_API_KEY",
    "API_KEY_OPENROUTER": "OPENROUTER_API_KEY",
    "API_KEY_HUGGINGFACE": "HUGGINGFACE_API_KEY",
}


def load_repo_env() -> list[str]:
    """Carica .env del repo senza loggare valori. Non sovrascrive os.environ già valorizzato."""
    here = os.path.dirname(os.path.abspath(__file__))
    dashboard = os.path.dirname(os.path.dirname(here))
    repo = os.path.dirname(dashboard)
    paths = [
        os.path.join(dashboard, ".env"),
        os.path.join(repo, ".env"),
        os.path.join(repo, "jarvis-bridge", ".env"),
        os.path.join(repo, "Agente-0", "config", "usr.env"),
    ]
    loaded_files = []
    for path in paths:
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for raw in fh:
                    line = raw.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    if line.lower().startswith("export "):
                        line = line[7:].strip()
                    name, _, val = line.partition("=")
                    name = name.strip().strip("'\"")
                    val = val.strip().strip("'\"")
                    if not name or not val:
                        continue
                    if not str(os.environ.get(name, "")).strip():
                        os.environ[name] = val
                    canon = _ALIASES.get(name)
                    if canon and not str(os.environ.get(canon, "")).strip():
                        os.environ[canon] = val
            loaded_files.append(os.path.basename(path))
        except OSError:
            continue
    return loaded_files


load_repo_env()


def _local_qwen_url() -> str:
    return os.environ.get("QWEN_LOCAL_URL", "http://127.0.0.1:61517/v1/chat/completions")


def _post_json(url: str, payload: dict, headers: dict, timeout: int = 20) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _chat_openai_compat(url: str, key: str, model: str, prompt: str, timeout: int = 20) -> str:
    body = _post_json(
        url,
        {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 1200},
        {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        timeout=timeout,
    )
    return body["choices"][0]["message"]["content"]


def _try_groq(prompt: str) -> str | None:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return None
    return _chat_openai_compat(
        "https://api.groq.com/openai/v1/chat/completions",
        key,
        os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
        prompt,
    )


def _try_gemini(prompt: str) -> str | None:
    key = (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if not key:
        return None
    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    body = _post_json(url, {"contents": [{"parts": [{"text": prompt}]}]}, {"Content-Type": "application/json"})
    return body["candidates"][0]["content"]["parts"][0]["text"]


def _try_openrouter(prompt: str) -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None
    return _chat_openai_compat(
        "https://openrouter.ai/api/v1/chat/completions",
        key,
        os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
        prompt,
    )


def _try_qwen38_openrouter(prompt: str) -> str | None:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None
    return _chat_openai_compat(
        "https://openrouter.ai/api/v1/chat/completions",
        key,
        os.environ.get("QWEN38_OPENROUTER_MODEL", "qwen/qwen3.8-max"),
        prompt,
        timeout=45,
    )


def _try_nvidia(prompt: str) -> str | None:
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        return None
    return _chat_openai_compat(
        os.environ.get(
            "NVIDIA_BASE_URL",
            "https://integrate.api.nvidia.com/v1/chat/completions",
        ),
        key,
        os.environ.get("NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"),
        prompt,
        timeout=40,
    )


def _try_ollama(prompt: str) -> str | None:
    base = (os.environ.get("OLLAMA_API_BASE") or os.environ.get("OLLAMA_HOST") or "http://127.0.0.1:11434").rstrip("/")
    if base.endswith("/v1"):
        url = f"{base}/chat/completions"
    else:
        url = f"{base}/v1/chat/completions"
    model = os.environ.get("HERMES_MODEL") or os.environ.get("OLLAMA_MODEL") or "hermes3:8b"
    try:
        return _chat_openai_compat(url, "ollama", model, prompt, timeout=40)
    except Exception:
        return None


def _try_hf(prompt: str) -> str | None:
    key = (os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY") or "").strip()
    if not key:
        return None
    model = os.environ.get("HF_CHAT_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    return _chat_openai_compat(
        "https://router.huggingface.co/v1/chat/completions",
        key,
        model,
        prompt,
    )


def _qwen_local_key() -> str:
    """Unsloth locale: UNSLOTH_API_KEY canonico, poi QWEN_API_KEY. Mai loggare."""
    return (os.environ.get("UNSLOTH_API_KEY") or os.environ.get("QWEN_API_KEY") or "").strip()


def _try_qwen_local(prompt: str) -> str | None:
    key = _qwen_local_key()
    if not key:
        return None
    try:
        return _chat_openai_compat(
            _local_qwen_url(),
            key,
            os.environ.get("QWEN_LOCAL_MODEL", "qwen"),
            prompt,
            timeout=25,
        )
    except Exception:
        return None


def _qwencloud_key() -> str:
    """DashScope/QwenCloud: non riusare la chiave Unsloth locale."""
    unsloth = os.environ.get("UNSLOTH_API_KEY", "").strip()
    dash = (os.environ.get("DASHSCOPE_API_KEY") or "").strip()
    qwen = (os.environ.get("QWEN_API_KEY") or "").strip()
    if dash:
        return dash
    if qwen and qwen != unsloth:
        return qwen
    return ""


def _try_qwencloud(prompt: str) -> str | None:
    key = _qwencloud_key()
    if not key:
        return None
    return _chat_openai_compat(
        os.environ.get(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        ),
        key,
        os.environ.get("QWEN_CLOUD_MODEL", "qwen3.8-max"),
        prompt,
        timeout=45,
    )


_STEPS = (
    ("groq", _try_groq),
    ("qwen3.8_openrouter", _try_qwen38_openrouter),
    ("nvidia", _try_nvidia),
    ("gemini", _try_gemini),
    ("ollama", _try_ollama),
    ("openrouter", _try_openrouter),
    ("huggingface", _try_hf),
    ("qwen_local", _try_qwen_local),
    ("qwencloud", _try_qwencloud),
)


def providers_set() -> dict:
    """Stato chiavi/provider: solo set / not set, mai i valori."""
    groq = bool(os.environ.get("GROQ_API_KEY", "").strip())
    gemini = bool((os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or "").strip())
    openrouter = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    hf = bool((os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_API_KEY") or "").strip())
    qwen_local = bool(_qwen_local_key())
    qwencloud = bool(_qwencloud_key())
    nvidia = bool(os.environ.get("NVIDIA_API_KEY", "").strip())
    ollama_base = (os.environ.get("OLLAMA_API_BASE") or os.environ.get("OLLAMA_HOST") or "").strip()
    tavily = bool(os.environ.get("TAVILY_API_KEY", "").strip())
    elevenlabs = bool(os.environ.get("ELEVENLABS_API_KEY", "").strip())
    return {
        "groq": "set" if groq else "not set",
        "qwen3.8_openrouter": "set" if openrouter else "not set",
        "nvidia": "set" if nvidia else "not set",
        "gemini": "set" if gemini else "not set",
        "ollama": "set" if ollama_base else "not set",
        "openrouter": "set" if openrouter else "not set",
        "huggingface": "set" if hf else "not set",
        "qwen_local": "set" if qwen_local else "not set",
        "qwencloud": "set" if qwencloud else "not set",
        "tavily_search": "set" if tavily else "not set",
        "elevenlabs_tts": "set" if elevenlabs else "not set",
    }


def execute(params=None):
    params = params or {}
    load_repo_env()
    if str(params.get("task") or "").strip().lower() in ("status", "providers"):
        return {"status": "SUCCESS", "providers": providers_set(), "tried": [s[0] for s in _STEPS]}
    prompt = str(params.get("prompt") or params.get("text") or "").strip()
    if not prompt:
        return {"status": "ERROR", "message": "Manca prompt.", "providers": providers_set()}
    skip = {str(x).strip().lower() for x in (params.get("skip") or [])}
    t0 = time.time()
    errors = []
    tried = []
    for name, fn in _STEPS:
        if name in skip:
            continue
        tried.append(name)
        try:
            text = fn(prompt)
            if text:
                return {
                    "status": "SUCCESS",
                    "provider": name,
                    "text": text,
                    "latency_ms": round((time.time() - t0) * 1000, 2),
                }
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, TimeoutError, OSError) as exc:
            errors.append({"provider": name, "error": type(exc).__name__})
    return {
        "status": "ERROR",
        "message": "Nessun provider AI ha risposto. Controlla le variabili in env.example.",
        "tried": tried,
        "errors": errors,
        "providers": providers_set(),
        "latency_ms": round((time.time() - t0) * 1000, 2),
    }
