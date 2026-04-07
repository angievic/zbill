---
layout: page
title: Eventos de tracking de ROI
permalink: /
---

**Zbill** analiza código en tu máquina y propone **dónde medir ROI** con métricas como `time_saved`, `errors_reduced` y `value_generated`.

[Ver el código en GitHub](https://github.com/angievic/zbill){: .btn }

---

## Instalación

```bash
git clone https://github.com/angievic/zbill.git
cd zbill
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
zbills --version
```

---

## Comandos

### Subcomandos

| Comando | Argumentos | Qué hace |
|--------|------------|----------|
| `zbills init` | `[path]` → default `.` | Crea **`.zbills.env.example`** (plantilla de variables para ingest y LLM). |
| `zbills analyze` | `[path]` → default `.` | Crea una carpeta única `…-zbill-runtime` con **`zbills_report.json`**, **`zbills_suggestions.md`** y **`zbills_runtime_report.html`**. |
| `zbills suggest` | `[path]` → default `.` | Usa el JSON en esa ruta o el informe más reciente en `**/*-zbill-runtime/`. |
| `zbills --version` | — | Muestra la versión instalada. |

### Opciones de `zbills analyze`

| Opción | Default | Descripción |
|--------|---------|-------------|
| `-o`, `--output-dir` | raíz analizada | Directorio **padre** donde se crea la subcarpeta `*-zbill-runtime`. |
| `--max` | sin límite | Tope de hallazgos (ordenados por score). |
| `--llm` | off | Enriquece los mejores hallazgos con un LLM. |
| `--provider` | variable de entorno | `ollama`, `openai`, `anthropic`, `gemini`. |
| `--model` | env / default del proveedor | Nombre del modelo (p. ej. `mistral`, `gpt-4o-mini`). |
| `--llm-top` | `15` | Cuántos hallazgos enviar al modelo. |

### Opciones de `zbills suggest`

| Opción | Default | Descripción |
|--------|---------|-------------|
| `--limit` | `20` | Máximo de entradas a imprimir. |

---

## Flujo recomendado

1. `zbills init` en la raíz del repo cliente.  
2. `zbills analyze .`  
3. Revisar `zbills_suggestions.md` o `zbills_report.json`.  
4. Opcional: `zbills analyze . --llm` (Ollama local por defecto).  
5. Abre `zbills_runtime_report.html` de la última carpeta `*-zbill-runtime`.  
6. `zbills suggest .` para ver ejemplos `track()` en consola.

---

## Lenguajes soportados

Python (AST), Go, JavaScript, TypeScript, Java y Ruby (heurísticas). Se saltan `node_modules`, `.git`, entornos virtuales y artefactos de build habituales.

---

## LLM y Ollama

- **Default**: proveedor `ollama`, modelo `mistral`.  
- **Cloud**: define la API key correspondiente y `ZBILLS_LLM_PROVIDER`.  
- **macOS/Linux**: si falta el modelo en Ollama, zbills puede ejecutar `ollama pull`.  
- **Windows**: se muestran instrucciones y enlace de descarga; el `pull` es manual.

Tabla rápida de variables:

| Variable | Rol |
|----------|-----|
| `ZBILLS_LLM_PROVIDER` | Proveedor activo. |
| `ZBILLS_LLM_MODEL` | Modelo. |
| `OPENAI_API_KEY` | OpenAI. |
| `ANTHROPIC_API_KEY` | Anthropic. |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | Gemini. |
| `OLLAMA_HOST` | URL del daemon Ollama. |

---

## Más detalle

El **README** del repositorio incluye la misma referencia ampliada (tablas, ejemplos y notas de Pages).

**Si en GitHub Pages no ves los colores crema / marrón:** en `_config.yml`, `baseurl` debe coincidir con el **nombre del repositorio** (p. ej. `"/zbill"`). En GitHub Actions el CSS también se resuelve con `site.github.url`. Tras corregir, espera el deploy y prueba recarga forzada (Ctrl+F5 / vaciar caché).
