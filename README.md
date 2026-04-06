# ZBILLS Analyzer

**ZBILLS** es una herramienta de línea de comandos que **escanea tu repositorio** y **sugiere dónde instrumentar métricas ROI** (`time_saved`, `errors_reduced`, `value_generated`) con ejemplos de `track()`.

- Análisis **estático** (AST en Python, heurísticas en Go, JavaScript, TypeScript, Java y Ruby).
- Capa **LLM opcional** (Ollama, OpenAI, Anthropic, Google Gemini) para refinar sugerencias.
- **Sin dependencias obligatorias** de terceros: el núcleo usa solo la biblioteca estándar de Python.

📖 **Documentación web**: publica la carpeta [`docs/`](./docs/) con [GitHub Pages](#github-pages). La URL será `https://<usuario>.github.io/<repositorio>/` (edita `url` y `baseurl` en `docs/_config.yml`).

---

## Requisitos

- Python **3.10+**
- (Opcional) [Ollama](https://ollama.com) u otras APIs si usas `--llm`

---

## Instalación

```bash
git clone https://github.com/YOUR_ORG/zbill.git
cd zbill
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
```

Comprueba la instalación:

```bash
zbills --version
python -m zbills --version
```

---

## Inicio rápido

```bash
cd tu-proyecto
zbills init              # crea .zbills.env.example
zbills analyze .         # crea carpeta *-zbill-runtime con JSON, MD e informe HTML
zbills suggest .         # usa el último informe bajo ese directorio (o el JSON en la ruta)
```

Con LLM local (Ollama + Mistral por defecto):

```bash
zbills analyze . --llm
```

---

## Comandos (referencia)

### Tabla de subcomandos

| Comando | Argumentos | Descripción |
|--------|------------|-------------|
| `zbills init` | `[path]` (por defecto `.`) | Crea `.zbills.env.example` en el directorio del proyecto con plantillas de variables (ingest, LLM, Ollama). No sobrescribe si el archivo ya existe. |
| `zbills analyze` | `[path]` (por defecto `.`) | Recorre el repo y crea una carpeta con nombre único que **termina en `-zbill-runtime`** (timestamp + UUID). Dentro escribe **`zbills_report.json`**, **`zbills_suggestions.md`** y **`zbills_runtime_report.html`**. Imprime resumen y la ruta de la carpeta. |
| `zbills suggest` | `[path]` (por defecto `.`) | Si existe `zbills_report.json` en la ruta, lo usa; si no, el **más reciente** bajo `**/*-zbill-runtime/zbills_report.json`. Muestra ejemplos `track()` por consola. |
| `zbills --version` | — | Muestra la versión del paquete. |

### Tabla de opciones: `zbills analyze`

| Opción | Tipo | Default | Descripción |
|--------|------|---------|-------------|
| `-o`, `--output-dir` | ruta | raíz analizada | **Directorio padre**: dentro se crea `YYYYMMDDTHHMMSSZ-<8hex>-zbill-runtime` con todos los artefactos. |
| `--max` | entero | sin límite | Máximo de hallazgos tras ordenar por puntuación (recorte del informe). |
| `--llm` | flag | desactivado | Activa el enriquecimiento con LLM sobre los mejores hallazgos. |
| `--provider` | texto | env | `ollama`, `openai`, `anthropic` o `gemini`. Tiene prioridad sobre `ZBILLS_LLM_PROVIDER`. |
| `--model` | texto | env / default por proveedor | Modelo concreto; prioridad sobre `ZBILLS_LLM_MODEL`. |
| `--llm-top` | entero | `15` | Cuántos hallazgos (desde el ranking) se envían al LLM. |

### Tabla de opciones: `zbills suggest`

| Opción | Tipo | Default | Descripción |
|--------|------|---------|-------------|
| `--limit` | entero | `20` | Máximo de hallazgos a mostrar desde el JSON. |

---

## Salidas generadas

Cada ejecución de `zbills analyze` crea **una carpeta nueva** con patrón:

`{UTC timestamp}T{hhmmss}Z-{8 hex}-zbill-runtime`

(por ejemplo `20260406T153022Z-a1b2c3d4-zbill-runtime`), dentro de la raíz analizada o de `--output-dir`.

| Archivo | Contenido |
|---------|-----------|
| `zbills_report.json` | Hallazgos ordenados; clave **`runtime`** (run id, carpetas, inicio/fin UTC, duración en s, versión, `--max`, si hubo LLM). Con `--llm`, también `llm` por hallazgo e informe. |
| `zbills_suggestions.md` | Misma información en Markdown; sección **Runtime** al inicio si aplica. |
| `zbills_runtime_report.html` | Informe visual del runtime y tabla de hallazgos (abrir en el navegador). |

---

## Lenguajes detectados

| Lenguaje | Extensiones | Enfoque |
|----------|-------------|---------|
| Python | `.py` | AST (`ast`): try/except, bucles, longitud de función, nombres alineados con negocio. |
| Go | `.go` | Heurísticas por firma `func` y ventana de líneas. |
| JavaScript | `.js`, `.mjs`, `.cjs`, `.jsx` | Heurísticas (`function`, `async function`, flechas `const x = () =>`). |
| TypeScript | `.ts`, `.tsx` | Igual que JS. |
| Java | `.java` | Heurísticas de métodos. |
| Ruby | `.rb` | Heurísticas `def`. |

Se ignoran directorios habituales: `node_modules`, `.git`, `venv`, `__pycache__`, `dist`, `build`, etc.

---

## Variables de entorno (LLM e ingest)

| Variable | Uso |
|----------|-----|
| `ZBILLS_LLM_PROVIDER` | `ollama` (default), `openai`, `anthropic`, `gemini`. |
| `ZBILLS_LLM_MODEL` | Modelo; si falta, hay un default por proveedor (p. ej. Ollama → `mistral`). |
| `OPENAI_API_KEY` / `ZBILLS_OPENAI_API_KEY` | OpenAI. |
| `ANTHROPIC_API_KEY` / `ZBILLS_ANTHROPIC_API_KEY` | Anthropic. |
| `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `ZBILLS_GEMINI_API_KEY` | Gemini. |
| `OLLAMA_HOST` / `ZBILLS_OLLAMA_URL` | Base URL del API de Ollama (default `http://127.0.0.1:11434`). |
| `ZBILLS_LLM_TIMEOUT` | Timeout en segundos (default `120`). |
| `ZBILLS_LLM_TEMPERATURE` | Temperatura (default `0.2`). |

Si eliges OpenAI, Anthropic o Gemini **sin** API key, el CLI muestra un mensaje con las variables a definir y la alternativa **Ollama local**.

### Ollama: modelo no instalado

- **macOS / Linux**: si el modelo no aparece en `/api/tags`, se ejecuta `ollama pull <modelo>` automáticamente (requiere `ollama` en el `PATH`).
- **Windows**: no se ejecuta `pull` desde zbills; se muestran instrucciones con enlace a la descarga de Ollama y el comando `ollama pull` manual.

---

## Ejemplos de uso

```bash
# Solo análisis estático, máximo 30 hallazgos
zbills analyze . --max 30

# LLM con OpenAI
export ZBILLS_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
zbills analyze . --llm --model gpt-4o-mini --llm-top 10

# LLM local explícito
zbills analyze . --llm --provider ollama --model mistral
```

---

## GitHub Pages

1. En el repositorio: **Settings → Pages**.
2. **Build and deployment**: Source **Deploy from a branch**.
3. Branch **main** (o la que uses), carpeta **`/docs`**.
4. Edita `docs/_config.yml`: sustituye `YOUR_GITHUB_USER` y `YOUR_REPO` en `url` y `baseurl`. Para un sitio de usuario (`username.github.io` sin subruta), usa `baseurl: ""`.
5. Tras el despliegue, la URL será `https://<usuario>.github.io/<repositorio>/`.

La documentación vive en [`docs/`](./docs/) (`index.md`, `_config.yml`). Vista previa local (opcional):

```bash
cd docs
bundle install
bundle exec jekyll serve
```

---

## Desarrollo

```bash
pip install -e ".[dev]"
pytest
```

---

## Licencia

MIT (ver `pyproject.toml`).

---

## Enlaces

- [Documentación (GitHub Pages)](https://YOUR_GITHUB_USER.github.io/YOUR_REPO/) — actualiza la URL en tu fork.
- [Ollama](https://ollama.com)
