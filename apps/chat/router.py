# =============================================================================
# CHAT API - Generic LLM Query Endpoint
# Uses local Ollama for inference
# =============================================================================

import os
import requests
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

router = APIRouter(tags=["Chat"])
templates = Jinja2Templates(directory="templates")

# Ollama configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.2:3b"

# Apps directory
APPS_DIR = "/var/www/fleminganalytic/apps"

# App descriptions for context
APP_DESCRIPTIONS = {
    "analyst": "Data analysis tool for CSV files with AI-powered insights",
    "astro": "Astronomy and astrology related calculations",
    "chat": "This chat interface for querying the local LLM",
    "fred": "Federal Reserve Economic Data (FRED) API integration",
    "news": "News aggregation and analysis",
    "orders": "Order management system",
    "restaurant": "Restaurant/food service management",
    "stocks": "Stock market data and analysis",
    "wordclouds": "Word cloud generation from text sources"
}


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def chat_page(request: Request):
    """Serve the chat interface"""
    return templates.TemplateResponse("chat.html", {"request": request})


class ChatRequest(BaseModel):
    prompt: str
    model: Optional[str] = DEFAULT_MODEL
    system: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096


class ChatResponse(BaseModel):
    response: str
    model: str
    done: bool
    tokens: Optional[int] = None
    tokens_per_second: Optional[float] = None
    eval_duration_ms: Optional[float] = None


@router.post("/query", response_model=ChatResponse)
async def query(request: ChatRequest):
    """
    Send a query to the local LLM and get a response.

    - **prompt**: Your question or instruction
    - **model**: Model to use (default: llama3.2:1b)
    - **system**: Optional system prompt to set context
    - **temperature**: Creativity (0.0-1.0, default 0.7)
    - **max_tokens**: Max response length (default 1024)
    """
    try:
        # Build the full prompt with optional system context
        full_prompt = request.prompt
        if request.system:
            full_prompt = f"System: {request.system}\n\nUser: {request.prompt}"

        payload = {
            "model": request.model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama error: {response.text}"
            )

        data = response.json()

        # Calculate tokens per second from Ollama's response
        eval_count = data.get("eval_count", 0)  # Number of tokens generated
        eval_duration = data.get("eval_duration", 0)  # Duration in nanoseconds

        tokens_per_second = None
        eval_duration_ms = None
        if eval_duration > 0:
            eval_duration_ms = eval_duration / 1_000_000  # Convert to ms
            tokens_per_second = round(eval_count / (eval_duration / 1_000_000_000), 2)

        return ChatResponse(
            response=data.get("response", ""),
            model=data.get("model", request.model),
            done=data.get("done", True),
            tokens=eval_count if eval_count > 0 else None,
            tokens_per_second=tokens_per_second,
            eval_duration_ms=round(eval_duration_ms, 1) if eval_duration_ms else None
        )

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama service not available. Is it running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timed out"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def list_models():
    """List available Ollama models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [
                {
                    "name": m["name"],
                    "size": m.get("size", 0),
                    "modified": m.get("modified_at", "")
                }
                for m in data.get("models", [])
            ]
            return {"models": models, "default": DEFAULT_MODEL}
        return {"models": [], "default": DEFAULT_MODEL}
    except Exception:
        return {"models": [], "default": DEFAULT_MODEL, "error": "Could not connect to Ollama"}


@router.get("/health")
async def health_check():
    """Check if Ollama is running and responsive"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            return {"status": "healthy", "ollama": "connected"}
        return {"status": "degraded", "ollama": "error"}
    except Exception:
        return {"status": "unhealthy", "ollama": "disconnected"}


# =============================================================================
# APP CODE ANALYSIS ENDPOINTS
# =============================================================================

class AppInfo(BaseModel):
    name: str
    description: str
    has_router: bool


class AppExplanation(BaseModel):
    app_name: str
    summary: str
    endpoints: List[str]
    explanation: str
    tokens: Optional[int] = None
    tokens_per_second: Optional[float] = None


def get_app_code(app_name: str) -> tuple[str, List[str]]:
    """Read all Python files from an app directory and extract endpoint paths"""
    app_path = os.path.join(APPS_DIR, app_name)

    if not os.path.isdir(app_path):
        raise HTTPException(status_code=404, detail=f"App '{app_name}' not found")

    code_content = []
    endpoints = []

    # Read all .py files in the app directory
    for filename in sorted(os.listdir(app_path)):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(app_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    code_content.append(f"# === {filename} ===\n{content}")

                    # Extract endpoint decorators
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('@router.') or line.startswith('@app.'):
                            if any(method in line for method in ['get(', 'post(', 'put(', 'delete(', 'patch(']):
                                # Extract the path from the decorator
                                start = line.find('("') or line.find("('")
                                if start > 0:
                                    start += 2
                                    end = line.find('"', start) if '"' in line[start:] else line.find("'", start)
                                    if end > start:
                                        path = line[start:end]
                                        method = line.split('.')[1].split('(')[0].upper()
                                        endpoints.append(f"{method} {path}")
            except Exception:
                continue

    if not code_content:
        raise HTTPException(status_code=404, detail=f"No Python code found in app '{app_name}'")

    return '\n\n'.join(code_content), endpoints


@router.get("/apps")
async def list_apps():
    """
    List all available apps that can be analyzed.

    Returns a list of app names with brief descriptions.
    """
    apps = []

    try:
        for item in sorted(os.listdir(APPS_DIR)):
            item_path = os.path.join(APPS_DIR, item)
            if os.path.isdir(item_path) and not item.startswith('__'):
                # Check if it has a router.py or similar
                has_router = any(
                    f.endswith('.py') and not f.startswith('__')
                    for f in os.listdir(item_path)
                )
                if has_router:
                    apps.append(AppInfo(
                        name=item,
                        description=APP_DESCRIPTIONS.get(item, "No description available"),
                        has_router=has_router
                    ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"apps": apps, "total": len(apps)}


@router.get("/explain/{app_name}", response_model=AppExplanation)
async def explain_app(app_name: str):
    """
    Analyze an app's code and explain what it does in human-readable terms.

    - **app_name**: Name of the app to analyze (e.g., 'analyst', 'stocks', 'fred')

    Uses the local LLM to read the app's source code and generate a
    plain-English explanation of its functionality.
    """
    # Get the app's code
    code, endpoints = get_app_code(app_name)

    # Truncate code if too long (LLM context limits)
    max_code_length = 8000
    if len(code) > max_code_length:
        code = code[:max_code_length] + "\n\n... [code truncated for length]"

    # Build the prompt for the LLM
    prompt = f"""Analyze this Python FastAPI application code and explain what it does in simple, human-readable terms.

App name: {app_name}
Known description: {APP_DESCRIPTIONS.get(app_name, 'Unknown')}

CODE:
{code}

Please provide:
1. A one-sentence summary of what this app does
2. The main features and capabilities
3. What kind of data it works with
4. Who might find this app useful

Keep your explanation clear and non-technical. Avoid code jargon."""

    try:
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more factual responses
                "num_predict": 1024
            }
        }

        response = requests.post(OLLAMA_URL, json=payload, timeout=120)

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama error: {response.text}"
            )

        data = response.json()

        # Calculate tokens per second
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 0)
        tokens_per_second = None
        if eval_duration > 0:
            tokens_per_second = round(eval_count / (eval_duration / 1_000_000_000), 2)

        return AppExplanation(
            app_name=app_name,
            summary=APP_DESCRIPTIONS.get(app_name, ""),
            endpoints=endpoints,
            explanation=data.get("response", ""),
            tokens=eval_count if eval_count > 0 else None,
            tokens_per_second=tokens_per_second
        )

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail="Ollama service not available. Is it running?"
        )
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timed out - the app code may be too large to analyze"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
