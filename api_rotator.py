#!/usr/bin/env python3
"""
EBJ Supreme - Multi-Provider API Rotator con Health Check Automatico
Gestisce rotazione, fallback e monitoraggio di tutte le chiavi API.
Supporta LLM testo e vision con cascata automatica.
"""

import os
import time
import json
import requests
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from pathlib import Path

class ProviderType(Enum):
    TEXT = "text"
    VISION = "vision"
    BOTH = "both"

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"

@dataclass
class APIKey:
    provider: str
    key: str
    key_type: ProviderType
    base_url: str
    models: List[str]
    env_var: str
    last_check: Optional[datetime] = None
    health: HealthStatus = HealthStatus.UNKNOWN
    latency_ms: Optional[float] = None
    error_count: int = 0
    success_count: int = 0
    
    def is_healthy(self) -> bool:
        return self.health == HealthStatus.HEALTHY
    
    def mark_success(self, latency_ms: float):
        self.success_count += 1
        self.error_count = max(0, self.error_count - 1)
        self.latency_ms = latency_ms
        self.last_check = datetime.utcnow()
        self.health = HealthStatus.HEALTHY
    
    def mark_failure(self):
        self.error_count += 1
        self.last_check = datetime.utcnow()
        if self.error_count >= 3:
            self.health = HealthStatus.DOWN
        elif self.error_count >= 1:
            self.health = HealthStatus.DEGRADED

@dataclass
class ProviderStats:
    provider: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    last_used: Optional[datetime] = None

class APIRotator:
    """Gestore rotazione API con health check automatico e fallback."""
    
    def __init__(self, env_file: Optional[str] = None):
        self.keys: Dict[str, APIKey] = {}
        self.stats: Dict[str, ProviderStats] = {}
        self.lock = threading.RLock()
        self.health_check_interval = 300  # 5 minuti
        self.last_health_check = datetime.utcnow() - timedelta(hours=1)
        
        if env_file:
            self._load_env_file(env_file)
        
        self._init_providers()
    
    def _load_env_file(self, env_file: str):
        """Carica variabili d'ambiente da file."""
        path = Path(env_file)
        if path.exists():
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ.setdefault(key, value)
    
    def _init_providers(self):
        """Inizializza tutti i provider con le chiavi dal .env."""
        
        # OpenRouter (2 chiavi) - Vision + Text
        for i, key_var in enumerate(['OPENROUTER_API_KEY', 'OPENROUTER_API_KEY_2'], 1):
            key = os.environ.get(key_var)
            if key:
                self.keys[f'openrouter_{i}'] = APIKey(
                    provider='openrouter',
                    key=key,
                    key_type=ProviderType.BOTH,
                    base_url='https://openrouter.ai/api/v1',
                    models=[
                        'google/gemma-4-26b-a4b-it:free',
                        'google/gemma-4-31b-it:free',
                        'minimax/minimax-m3:free',
                        'nvidia/nemotron-3.5-lightning:free',
                        'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
                        'nvidia/llama-3.1-nemotron-70b-instruct'
                    ],
                    env_var=key_var
                )
        
        # Groq (2 chiavi) - Text only (veloce)
        for i, key_var in enumerate(['GROQ_API_KEY', 'GROQ_API_KEY_2'], 1):
            key = os.environ.get(key_var)
            if key:
                self.keys[f'groq_{i}'] = APIKey(
                    provider='groq',
                    key=key,
                    key_type=ProviderType.TEXT,
                    base_url='https://api.groq.com/openai/v1',
                    models=['llama-3.1-8b-instant', 'llama-3.3-70b-versatile', 'mixtral-8x7b-32768'],
                    env_var=key_var
                )
        
        # DeepSeek - Text only
        key = os.environ.get('DEEPSEEK_API_KEY')
        if key:
            self.keys['deepseek'] = APIKey(
                provider='deepseek',
                key=key,
                key_type=ProviderType.TEXT,
                base_url='https://api.deepseek.com/v1',
                models=['deepseek-chat', 'deepseek-coder'],
                env_var='DEEPSEEK_API_KEY'
            )
        
        # OpenAI - Vision + Text
        key = os.environ.get('OPENAI_API_KEY')
        if key:
            self.keys['openai'] = APIKey(
                provider='openai',
                key=key,
                key_type=ProviderType.BOTH,
                base_url='https://api.openai.com/v1',
                models=['gpt-4-vision-preview', 'gpt-4-turbo', 'gpt-3.5-turbo'],
                env_var='OPENAI_API_KEY'
            )
        
        # Zhipu AI (GLM-4V) - Vision + Text
        key = os.environ.get('ZHIPU_API_KEY')
        if key:
            self.keys['zhipu'] = APIKey(
                provider='zhipu',
                key=key,
                key_type=ProviderType.BOTH,
                base_url='https://open.bigmodel.cn/api/paas/v4',
                models=['glm-4v', 'glm-4', 'glm-3-turbo'],
                env_var='ZHIPU_API_KEY'
            )
        
        # SiliconFlow - Vision + Text
        key = os.environ.get('SILICONFLOW_API_KEY')
        if key:
            self.keys['siliconflow'] = APIKey(
                provider='siliconflow',
                key=key,
                key_type=ProviderType.BOTH,
                base_url='https://api.siliconflow.cn/v1',
                models=['Qwen/Qwen2.5-7B-Instruct', 'Qwen/Qwen2-VL-7B-Instruct'],
                env_var='SILICONFLOW_API_KEY'
            )
        
        # NVIDIA - Text only
        key = os.environ.get('NVIDIA_API_KEY')
        if key:
            self.keys['nvidia'] = APIKey(
                provider='nvidia',
                key=key,
                key_type=ProviderType.TEXT,
                base_url='https://integrate.api.nvidia.com/v1',
                models=[
                    'nvidia/nemotron-3.5-lightning',
                    'nvidia/llama-3.1-nemotron-70b-instruct',
                    'nvidia/nemotron-4-340b-instruct',
                    'meta/llama-3.1-70b-instruct'
                ],
                env_var='NVIDIA_API_KEY'
            )
        
        # HuggingFace - Vision + Text
        key = os.environ.get('HF_API_KEY')
        if key:
            self.keys['huggingface'] = APIKey(
                provider='huggingface',
                key=key,
                key_type=ProviderType.BOTH,
                base_url='https://api-inference.huggingface.co',
                models=['microsoft/DialoGPT-medium', 'nlpconnect/vit-gpt2-image-captioning'],
                env_var='HF_API_KEY'
            )
        
        # Gemini - Vision + Text (GRATUITO, prioritario)
        key = os.environ.get('GEMINI_API_KEY')
        if key:
            self.keys['gemini'] = APIKey(
                provider='gemini',
                key=key,
                key_type=ProviderType.BOTH,
                base_url='https://generativelanguage.googleapis.com/v1beta',
                models=['gemini-flash-latest', 'gemini-flash-lite-latest', 'gemini-pro'],
                env_var='GEMINI_API_KEY'
            )
        
        # Inizializza stats
        for key_name in self.keys:
            self.stats[key_name] = ProviderStats(provider=key_name)
    
    def health_check(self, force: bool = False) -> Dict[str, HealthStatus]:
        """Esegue health check su tutte le chiavi."""
        now = datetime.utcnow()
        if not force and (now - self.last_health_check).total_seconds() < self.health_check_interval:
            return {k: v.health for k, v in self.keys.items()}
        
        print(f"[API Rotator] Esecuzione health check su {len(self.keys)} chiavi...")
        
        for key_name, api_key in self.keys.items():
            self._check_single_key(key_name, api_key)
        
        self.last_health_check = now
        return {k: v.health for k, v in self.keys.items()}
    
    def _check_single_key(self, key_name: str, api_key: APIKey):
        """Testa una singola chiave con una chiamata reale."""
        try:
            start = time.time()
            
            # Scegli il modello in base al tipo
            if api_key.key_type == ProviderType.VISION:
                model = api_key.models[0]
                payload = self._build_vision_test_payload(api_key.provider, model)
            else:
                model = api_key.models[0]
                payload = self._build_text_test_payload(api_key.provider, model)
            
            response = self._make_request(api_key, payload, timeout=10)
            latency_ms = (time.time() - start) * 1000
            
            if response and response.status_code == 200:
                api_key.mark_success(latency_ms)
                print(f"  ✓ {key_name}: OK ({latency_ms:.0f}ms)")
            else:
                api_key.mark_failure()
                print(f"  ✗ {key_name}: FAIL (HTTP {response.status_code if response else 'N/A'})")
        
        except Exception as e:
            api_key.mark_failure()
            print(f"  ✗ {key_name}: ERROR ({e})")
    
    def _build_text_test_payload(self, provider: str, model: str) -> Dict:
        """Crea payload di test per testo."""
        if provider == 'gemini':
            return {
                'model': model,
                'contents': [{'parts': [{'text': 'Test'}]}]
            }
        else:
            return {
                'model': model,
                'messages': [{'role': 'user', 'content': 'Test'}],
                'max_tokens': 10
            }
    
    def _build_vision_test_payload(self, provider: str, model: str) -> Dict:
        """Crea payload di test per vision."""
        # Test image: 1x1 pixel bianco in base64
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        if provider == 'gemini':
            return {
                'model': model,
                'contents': [{
                    'parts': [
                        {'text': 'Descrivi questa immagine'},
                        {'inlineData': {'mimeType': 'image/png', 'data': test_image_b64}}
                    ]
                }]
            }
        else:
            return {
                'model': model,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': 'Descrivi questa immagine'},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{test_image_b64}'}}
                    ]
                }],
                'max_tokens': 50
            }
    
    def _make_request(self, api_key: APIKey, payload: Dict, timeout: int = 30) -> Optional[requests.Response]:
        """Esegue la richiesta HTTP al provider."""
        headers = {
            'Content-Type': 'application/json',
        }
        
        # Auth header diverso per provider
        if api_key.provider == 'gemini':
            url = f"{api_key.base_url}/models/{payload['model']}:generateContent?key={api_key.key}"
            payload.pop('model', None)
        else:
            headers['Authorization'] = f"Bearer {api_key.key}"
            url = f"{api_key.base_url}/chat/completions"
        
        try:
            return requests.post(url, json=payload, headers=headers, timeout=timeout)
        except:
            return None
    
    def get_healthy_keys(self, key_type: Optional[ProviderType] = None) -> List[APIKey]:
        """Restituisce le chiavi funzionanti, ordinate per latenza."""
        with self.lock:
            keys = [k for k in self.keys.values() if k.is_healthy()]
            
            if key_type:
                keys = [k for k in keys if k.key_type == key_type or k.key_type == ProviderType.BOTH]
            
            # Ordina per latenza (più veloce prima)
            return sorted(keys, key=lambda k: k.latency_ms or 999999)
    
    def call(
        self,
        prompt: str,
        image_b64: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Esegue una chiamata API con rotazione automatica.
        
        Args:
            prompt: Testo del prompt
            image_b64: Immagine base64 (opzionale, per vision)
            model: Modello specifico (opzionale)
            provider: Provider specifico (opzionale)
            timeout: Timeout in secondi
            max_retries: Numero massimo di tentativi
        
        Returns:
            Tuple[response_dict, error_message]
        """
        
        # Determina il tipo di chiamata
        key_type = ProviderType.VISION if image_b64 else ProviderType.TEXT
        
        # Health check se necessario
        self.health_check()
        
        # Ottieni chiavi funzionanti
        if provider:
            candidates = [k for k in self.keys.values() if k.provider == provider and k.is_healthy()]
        else:
            candidates = self.get_healthy_keys(key_type)
        
        if not candidates:
            return None, "Nessun provider funzionante disponibile"
        
        # Prova ogni chiave con retry
        for attempt in range(max_retries):
            for api_key in candidates:
                response, error = self._call_single(api_key, prompt, image_b64, model, timeout)
                
                if response:
                    # Aggiorna stats
                    with self.lock:
                        stats = self.stats[api_key.env_var]
                        stats.total_requests += 1
                        stats.successful_requests += 1
                        stats.last_used = datetime.utcnow()
                    
                    return response, None
                else:
                    # Key fallita, prova la prossima
                    continue
            
            # Tutte le chiavi fallite, aspetta prima di riprovare
            if attempt < max_retries - 1:
                time.sleep(1 * (attempt + 1))
        
        return None, "Tutti i tentativi falliti"
    
    def _call_single(
        self,
        api_key: APIKey,
        prompt: str,
        image_b64: Optional[str],
        model: Optional[str],
        timeout: int
    ) -> Tuple[Optional[Dict], Optional[str]]:
        """Chiama un singolo provider."""
        try:
            start = time.time()
            
            # Build payload
            if image_b64:
                payload = self._build_vision_payload(api_key, prompt, image_b64, model)
            else:
                payload = self._build_text_payload(api_key, prompt, model)
            
            # Make request
            response = self._make_request(api_key, payload, timeout)
            latency_ms = (time.time() - start) * 1000
            
            if response and response.status_code == 200:
                api_key.mark_success(latency_ms)
                return response.json(), None
            else:
                api_key.mark_failure()
                return None, f"HTTP {response.status_code if response else 'N/A'}"
        
        except Exception as e:
            api_key.mark_failure()
            return None, str(e)
    
    def _build_text_payload(self, api_key: APIKey, prompt: str, model: Optional[str]) -> Dict:
        """Crea payload per chiamata testo."""
        model = model or api_key.models[0]
        
        if api_key.provider == 'gemini':
            return {
                'model': model,
                'contents': [{'parts': [{'text': prompt}]}]
            }
        else:
            return {
                'model': model,
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 1000
            }
    
    def _build_vision_payload(self, api_key: APIKey, prompt: str, image_b64: str, model: Optional[str]) -> Dict:
        """Crea payload per chiamata vision."""
        model = model or api_key.models[0]
        
        if api_key.provider == 'gemini':
            return {
                'model': model,
                'contents': [{
                    'parts': [
                        {'text': prompt},
                        {'inlineData': {'mimeType': 'image/jpeg', 'data': image_b64}}
                    ]
                }]
            }
        else:
            return {
                'model': model,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_b64}'}}
                    ]
                }],
                'max_tokens': 1000
            }
    
    def get_stats(self) -> Dict[str, Dict]:
        """Restituisce le statistiche di tutti i provider."""
        with self.lock:
            return {
                name: {
                    'provider': stats.provider,
                    'total': stats.total_requests,
                    'successful': stats.successful_requests,
                    'failed': stats.failed_requests,
                    'avg_latency_ms': stats.avg_latency_ms,
                    'last_used': stats.last_used.isoformat() if stats.last_used else None,
                    'health': self.keys[name].health.value,
                    'latency_ms': self.keys[name].latency_ms
                }
                for name, stats in self.stats.items()
            }
    
    def force_health_check(self):
        """Forza un health check immediato."""
        return self.health_check(force=True)

# Singleton globale
_rotator_instance: Optional[APIRotator] = None

def get_rotator(env_file: Optional[str] = None) -> APIRotator:
    """Ottiene l'istanza singleton del rotator."""
    global _rotator_instance
    if _rotator_instance is None:
        _rotator_instance = APIRotator(env_file)
    return _rotator_instance

def call_api(
    prompt: str,
    image_b64: Optional[str] = None,
    provider: Optional[str] = None,
    **kwargs
) -> Tuple[Optional[Dict], Optional[str]]:
    """Funzione helper per chiamata rapida."""
    rotator = get_rotator()
    return rotator.call(prompt, image_b64, provider=provider, **kwargs)

if __name__ == "__main__":
    # Test
    rotator = APIRotator()
    print(f"Inizializzati {len(rotator.keys)} provider")
    
    # Health check
    print("\nHealth check:")
    rotator.force_health_check()
    
    # Stats
    print("\nStatistiche:")
    print(json.dumps(rotator.get_stats(), indent=2, default=str))
