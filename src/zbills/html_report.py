from __future__ import annotations

import base64
import html
import json
from pathlib import Path

from zbills.models import AnalysisReport


def _embed_payload(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def write_runtime_html(report: AnalysisReport, path: Path) -> None:
    """Informe HTML interactivo: datos = mismo JSON que zbills_report.json (embebido en Base64)."""
    data = report.to_dict()
    payload_b64 = _embed_payload(data)
    rt = report.runtime or {}
    run_id_esc = html.escape(str(rt.get("run_id", "zbills")))

    doc = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="theme-color" content="#faf7f2" />
  <title>Zbill — Eventos de tracking de ROI — {run_id_esc}</title>
  <style>
    :root {{
      --bg: #faf7f2;
      --bg-deep: #f3ece4;
      --card: #ffffff;
      --text: #1c1917;
      --muted: #57534e;
      --muted-warm: #6b5d4f;
      --accent: #6b4423;
      --accent-mid: #8b5c2e;
      --accent-soft: #a67c52;
      --accent-light: #c4a574;
      --border: #e7e5e4;
      --border-warm: #d4c4b0;
      --note: #b45309;
      --danger: #b91c1c;
      --code-bg: #f5f0e8;
      --code-text: #44403c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      color: var(--text);
      line-height: 1.55;
      min-height: 100vh;
      background: linear-gradient(180deg, var(--bg) 0%, var(--bg-deep) 100%);
    }}
    header {{
      padding: 1.75rem 1.25rem;
      border-bottom: 1px solid var(--border-warm);
      background: linear-gradient(180deg, #ffffff 0%, rgba(250, 247, 242, 0.95) 100%);
      box-shadow: 0 1px 0 var(--border);
    }}
    header h1 {{
      margin: 0 0 0.35rem;
      font-size: 1.35rem;
      color: var(--text);
      padding-bottom: 0.35rem;
      border-bottom: 2px solid var(--accent-light);
      display: inline-block;
    }}
    header p {{ margin: 0; color: var(--muted); font-size: 0.95rem; }}
    main {{ max-width: 960px; margin: 0 auto; padding: 1.25rem 1.25rem 2rem; }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border-warm);
      border-radius: 10px;
      padding: 1rem 1.15rem;
      margin-bottom: 1rem;
      box-shadow: 0 2px 12px rgba(107, 68, 35, 0.06);
    }}
    .card h2 {{
      margin: 0 0 0.75rem;
      font-size: 1.05rem;
      color: var(--muted-warm);
      font-weight: 700;
    }}
    dl.grid {{
      display: grid;
      grid-template-columns: 12rem 1fr;
      gap: 0.35rem 1rem;
      margin: 0;
    }}
    dt {{ color: var(--muted); font-size: 0.88rem; }}
    dd {{ margin: 0; color: var(--text); }}
    code {{
      font-size: 0.88em;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: var(--code-bg);
      color: var(--code-text);
      padding: 0.12em 0.4em;
      border-radius: 4px;
      border: 1px solid var(--border);
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
      align-items: center;
    }}
    .controls label {{ font-size: 0.85rem; color: var(--muted); }}
    #search {{
      flex: 1;
      min-width: 14rem;
      padding: 0.5rem 0.65rem;
      border: 1px solid var(--border-warm);
      border-radius: 8px;
      font-size: 0.95rem;
      background: #fffefb;
    }}
    #search:focus {{
      outline: 2px solid var(--accent-soft);
      outline-offset: 1px;
    }}
    #metric-filter {{
      padding: 0.45rem 0.5rem;
      border-radius: 8px;
      border: 1px solid var(--border-warm);
      background: #fffefb;
      color: var(--text);
    }}
    .btn-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; }}
    .btn {{
      cursor: pointer;
      padding: 0.45rem 0.75rem;
      border-radius: 8px;
      border: 1px solid var(--border-warm);
      background: linear-gradient(180deg, #fffefb, #f5f0e8);
      color: var(--accent-mid);
      font-size: 0.85rem;
      font-weight: 600;
    }}
    .btn:hover {{
      border-color: var(--accent-soft);
      color: var(--accent);
      background: #fffefb;
    }}
    #count-badge {{
      font-size: 0.88rem;
      color: var(--muted);
    }}
    #count-badge strong {{ color: var(--accent-mid); }}
    details.finding {{
      background: var(--card);
      border: 1px solid var(--border-warm);
      border-radius: 10px;
      padding: 0;
      margin-bottom: 0.65rem;
      box-shadow: 0 2px 12px rgba(107, 68, 35, 0.06);
    }}
    details.finding[open] {{ background: #fffefb; }}
    details.finding > summary {{
      cursor: pointer;
      list-style: none;
      padding: 0.85rem 1rem;
      font-weight: 600;
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 0.35rem 0.5rem;
    }}
    details.finding > summary::-webkit-details-marker {{ display: none; }}
    details.finding > summary::before {{
      content: "▸";
      display: inline-block;
      width: 1rem;
      color: var(--accent-soft);
      transition: transform 0.15s;
    }}
    details.finding[open] > summary::before {{ transform: rotate(90deg); }}
    .fi-idx {{ color: var(--muted); font-weight: 700; min-width: 1.5rem; }}
    .finding-body {{ padding: 0 1rem 1rem; }}
    .meta {{ color: var(--muted); font-weight: normal; font-size: 0.85rem; }}
    h2.section-title {{
      font-size: 1.1rem;
      margin: 1.25rem 0 0.5rem;
      color: var(--muted-warm);
      font-weight: 700;
    }}
    table.sug {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
      margin-top: 0.5rem;
      border: 1px solid var(--border-warm);
      border-radius: 8px;
      overflow: hidden;
    }}
    table.sug th, table.sug td {{
      border: 1px solid var(--border-warm);
      padding: 0.5rem 0.55rem;
      vertical-align: top;
    }}
    table.sug th {{
      background: #f5f0e8;
      text-align: left;
      color: var(--muted-warm);
      font-weight: 600;
      font-size: 0.82rem;
    }}
    table.sug tbody tr:hover {{ background: rgba(139, 92, 46, 0.06); }}
    table.sug td code {{ word-break: break-word; }}
    .llm-ok {{
      color: var(--accent-mid);
      font-size: 0.9rem;
      padding: 0.5rem 0.65rem;
      background: #fffefb;
      border-radius: 6px;
      border-left: 3px solid var(--accent-soft);
      margin-bottom: 0.5rem;
    }}
    .llm-err {{
      color: var(--danger);
      font-size: 0.9rem;
      padding: 0.5rem 0.65rem;
      background: #fffefb;
      border-radius: 6px;
      border-left: 3px solid var(--danger);
      margin-bottom: 0.5rem;
    }}
    .process-note {{
      color: var(--note);
      font-size: 0.88rem;
      margin-top: 0.75rem;
    }}
    details.json-panel > summary {{
      cursor: pointer;
      font-weight: 700;
      color: var(--muted-warm);
      padding: 0.25rem 0;
    }}
    #json-pretty {{
      margin: 0.75rem 0 0;
      padding: 1rem;
      background: var(--code-bg);
      color: var(--code-text);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: auto;
      max-height: 50vh;
      font-size: 0.78rem;
      line-height: 1.45;
    }}
    .json-tree {{
      font-family: ui-monospace, Menlo, Consolas, monospace;
      font-size: 0.8rem;
      margin-top: 0.5rem;
    }}
    .json-node {{
      margin: 0.15rem 0 0.15rem 0.5rem;
      padding-left: 0.5rem;
      border-left: 2px solid var(--border-warm);
    }}
    .json-node > summary {{
      cursor: pointer;
      color: var(--accent-mid);
      font-weight: 600;
    }}
    .json-row {{ margin: 0.2rem 0 0.2rem 0.25rem; }}
    .json-k {{ color: var(--muted-warm); font-weight: 600; }}
    .json-scalar {{ color: var(--code-text); word-break: break-word; }}
    footer {{
      padding: 1.5rem;
      text-align: center;
      color: var(--muted);
      font-size: 0.85rem;
      border-top: 1px solid var(--border-warm);
      background: linear-gradient(180deg, transparent, var(--bg-deep));
    }}
    a {{ color: var(--accent-mid); text-decoration: none; }}
    a:hover {{ color: var(--accent); text-decoration: underline; }}
    .metrics-tabs-wrap {{
      margin-bottom: 1rem;
      padding: 0;
      overflow: hidden;
    }}
    .tab-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 0;
      border-bottom: 1px solid var(--border-warm);
      background: linear-gradient(180deg, #fffefb, #faf7f2);
    }}
    .tab-btn {{
      flex: 1 1 0;
      min-width: 8rem;
      margin: 0;
      padding: 0.65rem 0.85rem;
      font-size: 0.92rem;
      font-weight: 600;
      font-family: inherit;
      cursor: pointer;
      border: none;
      border-bottom: 3px solid transparent;
      background: transparent;
      color: var(--muted);
      transition: color 0.15s, border-color 0.15s, background 0.15s;
    }}
    .tab-btn:hover {{
      color: var(--text);
      background: rgba(139, 92, 46, 0.06);
    }}
    .tab-btn.tab-btn-active {{
      color: var(--text);
      background: #fffefb;
      border-bottom-color: var(--accent-soft);
    }}
    .tab-btn.tab-impact.tab-btn-active {{ border-bottom-color: #22c55e; color: #166534; }}
    .tab-btn.tab-cost.tab-btn-active {{ border-bottom-color: #ea580c; color: #9a3412; }}
    .tab-btn.tab-roi.tab-btn-active {{ border-bottom-color: var(--accent-mid); color: var(--accent); }}
    .tab-panel-wrap {{
      padding: 1rem 1.15rem 1.15rem;
      background: var(--card);
    }}
    .tab-panel[hidden] {{
      display: none !important;
    }}
    .impact-card h2 {{
      margin: 0 0 0.75rem;
      font-size: 1.05rem;
      color: #166534;
      padding-bottom: 0.35rem;
      border-bottom: 2px solid #22c55e;
    }}
    .cost-card h2 {{
      margin: 0 0 0.75rem;
      font-size: 1.05rem;
      color: #9a3412;
      padding-bottom: 0.35rem;
      border-bottom: 2px solid #ea580c;
    }}
    .roi-card h2 {{
      margin: 0 0 0.5rem;
      font-size: 1.05rem;
      color: var(--muted-warm);
    }}
    .roi-formula {{
      font-family: ui-monospace, Menlo, Consolas, monospace;
      font-size: 0.9rem;
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.65rem 0.85rem;
      color: var(--code-text);
    }}
    noscript {{
      display: block;
      padding: 1rem;
      margin: 1rem;
      background: #fffefb;
      border: 1px solid var(--border-warm);
      border-radius: 8px;
      color: var(--note);
    }}
    @media print {{
      body {{ background: #fff; }}
      .card, details.finding {{ box-shadow: none; break-inside: avoid; }}
      .controls, #json-interactive {{ display: none; }}
      .metrics-tabs-wrap .tab-row {{ display: none; }}
      .metrics-tabs-wrap .tab-panel {{ display: block !important; }}
      .metrics-tabs-wrap .tab-panel[hidden] {{ display: block !important; }}
      .metrics-tabs-wrap .tab-panel + .tab-panel {{ margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-warm); }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Zbill — Eventos de tracking de ROI</h1>
    <p id="header-sub">Informe de runtime · vista interactiva · datos embebidos (<code>zbills_report.json</code>)</p>
  </header>
  <noscript>Activa JavaScript para filtrar hallazgos y explorar el JSON.</noscript>
  <main>
    <div id="mount-runtime"></div>
    <div id="mount-llm"></div>
    <section class="card" id="mount-summary"></section>
    <section class="card metrics-tabs-wrap" id="metrics-tabs-wrap" style="display:none" aria-label="Métricas por pestaña">
      <div class="tab-row" role="tablist" aria-label="Impacto, costo y ROI">
        <button type="button" class="tab-btn tab-impact tab-btn-active" role="tab" id="tab-btn-impact" aria-selected="true" aria-controls="panel-impact" tabindex="0">Impact metrics</button>
        <button type="button" class="tab-btn tab-cost" role="tab" id="tab-btn-cost" aria-selected="false" aria-controls="panel-cost" tabindex="-1">Cost metrics</button>
        <button type="button" class="tab-btn tab-roi" role="tab" id="tab-btn-roi" aria-selected="false" aria-controls="panel-roi" tabindex="-1">ROI preview</button>
      </div>
      <div class="tab-panel-wrap">
        <div id="panel-impact" class="tab-panel impact-card" role="tabpanel" aria-labelledby="tab-btn-impact"></div>
        <div id="panel-cost" class="tab-panel cost-card" role="tabpanel" aria-labelledby="tab-btn-cost" hidden></div>
        <div id="panel-roi" class="tab-panel roi-card" role="tabpanel" aria-labelledby="tab-btn-roi" hidden></div>
      </div>
    </section>
    <section class="card controls" id="toolbar" hidden>
      <input type="search" id="search" placeholder="Buscar en archivo, función, métrica, razón…" autocomplete="off" />
      <label>Métrica <select id="metric-filter"><option value="">Todas</option></select></label>
      <span id="count-badge"></span>
      <div class="btn-row">
        <button type="button" class="btn" id="btn-expand">Expandir hallazgos</button>
        <button type="button" class="btn" id="btn-collapse">Colapsar hallazgos</button>
        <button type="button" class="btn" id="btn-copy-json">Copiar JSON</button>
      </div>
    </section>
    <h2 class="section-title">Hallazgos</h2>
    <div id="findings-root"></div>
    <details class="card json-panel" id="json-interactive">
      <summary>Explorar JSON (árbol interactivo)</summary>
      <p class="process-note" style="margin-top:0.5rem">Misma estructura que <code>zbills_report.json</code>. Clic en nodos para expandir.</p>
      <div id="json-tree" class="json-tree"></div>
    </details>
    <details class="card json-panel">
      <summary>JSON formateado (texto)</summary>
      <pre id="json-pretty"></pre>
    </details>
  </main>
  <footer>Generado por Zbill · datos locales embebidos en esta página</footer>
  <script type="text/plain" id="zbills-b64" style="display:none">{payload_b64}</script>
  <script>
(function () {{
  function decodePayload() {{
    const b64 = document.getElementById("zbills-b64").textContent.trim();
    const bin = atob(b64);
    const u8 = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
    return JSON.parse(new TextDecoder("utf-8").decode(u8));
  }}

  function el(tag, cls, text) {{
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null && text !== "") e.textContent = text;
    return e;
  }}

  function appendCode(parent, value) {{
    const c = el("code", null, String(value));
    parent.appendChild(c);
  }}

  function buildRuntimeCard(data) {{
    const rt = data.runtime || {{}};
    const card = el("section", "card");
    card.appendChild(el("h2", null, "Runtime"));
    const dl = el("dl", "grid");
    const rows = [
      ["Run ID (carpeta)", rt.run_id],
      ["Ruta de salida", rt.run_folder],
      ["Proyecto analizado", rt.analyzed_root || data.root],
      ["Inicio (UTC)", rt.started_at],
      ["Fin (UTC)", rt.finished_at],
      ["Duración (s)", rt.duration_seconds],
      ["Versión zbills", rt.zbills_version],
      ["Tope --max", rt.max_findings != null ? String(rt.max_findings) : "sin límite"],
      ["LLM activo", rt.llm_enabled ? "Sí" : "No"],
    ];
    for (const [k, v] of rows) {{
      dl.appendChild(el("dt", null, k));
      const dd = el("dd");
      if (k.includes("carpeta") || k.includes("Ruta") || k.includes("Proyecto")) {{
        appendCode(dd, v != null ? v : "—");
      }} else {{
        dd.textContent = v != null && v !== "" ? String(v) : "—";
      }}
      dl.appendChild(dd);
    }}
    card.appendChild(dl);
    return card;
  }}

  function buildLlmCard(data) {{
    const L = data.llm;
    if (!L || !L.enabled) return null;
    const card = el("section", "card");
    card.appendChild(el("h2", null, "LLM"));
    const dl = el("dl", "grid");
    [["Proveedor", L.provider], ["Modelo", L.model], ["Hallazgos enriquecidos (top)", L.enriched_top]].forEach(([k, v]) => {{
      dl.appendChild(el("dt", null, k));
      const dd = el("dd");
      dd.textContent = v != null ? String(v) : "—";
      dl.appendChild(dd);
    }});
    card.appendChild(dl);
    return card;
  }}

  function buildSummaryCard(data) {{
    const card = el("section", "card");
    card.appendChild(el("h2", null, "Resumen"));
    const n = (data.findings || []).length;
    const p1 = el("p", null, "");
    p1.appendChild(el("strong", null, String(n)));
    p1.appendChild(document.createTextNode(" oportunidades ROI detectadas."));
    card.appendChild(p1);
    const p2 = el("p", null, "");
    p2.appendChild(document.createTextNode("Archivos en esta carpeta: "));
    ["zbills_report.json", "zbills_suggestions.md", "zbills_runtime_report.html"].forEach((name, i) => {{
      if (i) p2.appendChild(document.createTextNode(", "));
      p2.appendChild(el("code", null, name));
    }});
    p2.appendChild(document.createTextNode("."));
    card.appendChild(p2);
    const note = el("p", "process-note", "Cada corrida genera una carpeta nueva …-zbill-runtime; úsala para auditar o comparar análisis.");
    card.appendChild(note);
    return card;
  }}

  function metricsFromFinding(f) {{
    return (f.suggestions || []).map((s) => s.metric).filter(Boolean);
  }}

  function suggestionText(s) {{
    return (s && (s.suggestion || s.example)) ? String(s.suggestion || s.example) : "";
  }}

  function categoryForSuggestion(s) {{
    const c = (s && s.category) ? String(s.category).toLowerCase() : "";
    if (c === "impact" || c === "cost") return c;
    const m = (s && s.metric) ? String(s.metric) : "";
    if (["time_saved", "errors_reduced", "value_generated"].includes(m)) return "impact";
    if (m && m.indexOf("cost_") === 0) return "cost";
    return "";
  }}

  function haystackForFinding(f) {{
    const parts = [f.file, f.function, f.language, String(f.line)];
    (f.suggestions || []).forEach((s) => {{
      parts.push(s.metric, s.reason, suggestionText(s), categoryForSuggestion(s));
    }});
    if (f.llm) parts.push(JSON.stringify(f.llm));
    return parts.join("\\n");
  }}

  function buildImpactCostRoi(data) {{
    const findings = data.findings || [];
    const impactRows = [];
    const costRows = [];
    findings.forEach((f) => {{
      (f.suggestions || []).forEach((s) => {{
        const cat = categoryForSuggestion(s);
        if (cat === "impact") impactRows.push({{ f: f, s: s }});
        else if (cat === "cost") costRows.push({{ f: f, s: s }});
      }});
    }});

    function fillSection(sectionEl, title, rows) {{
      sectionEl.innerHTML = "";
      sectionEl.appendChild(el("h2", null, title));
      if (rows.length === 0) {{
        sectionEl.appendChild(el("p", "meta", "Sin sugerencias en esta categoría."));
        return;
      }}
      const tbl = document.createElement("table");
      tbl.className = "sug";
      tbl.innerHTML = "<thead><tr><th>Archivo</th><th>Línea</th><th>Función</th><th>Métrica</th><th>Razón</th></tr></thead><tbody></tbody>";
      const tb = tbl.querySelector("tbody");
      rows.forEach((row) => {{
        const f = row.f;
        const s = row.s;
        const tr = document.createElement("tr");
        const td0 = document.createElement("td");
        td0.appendChild(el("code", null, f.file || ""));
        const tdL = document.createElement("td");
        tdL.textContent = f.line != null ? String(f.line) : "—";
        const td1 = document.createElement("td");
        td1.appendChild(el("code", null, f.function || ""));
        const td2 = document.createElement("td");
        td2.appendChild(el("code", null, s.metric || ""));
        const td3 = document.createElement("td");
        td3.textContent = s.reason || "";
        tr.appendChild(td0);
        tr.appendChild(tdL);
        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);
        tb.appendChild(tr);
      }});
      sectionEl.appendChild(tbl);
    }}

    const mi = document.getElementById("panel-impact");
    const mc = document.getElementById("panel-cost");
    const mr = document.getElementById("panel-roi");
    const wrap = document.getElementById("metrics-tabs-wrap");
    fillSection(mi, "Impact metrics (ROI numerator)", impactRows);
    fillSection(mc, "Cost metrics (ROI denominator)", costRows);
    wrap.style.display = findings.length ? "" : "none";

    mr.innerHTML = "";
    mr.appendChild(el("h2", null, "ROI preview (referencia)"));
    const p = document.createElement("p");
    p.appendChild(document.createTextNode("Con eventos en Zpulse, "));
    p.appendChild(el("code", null, "GET .../api/v1/summary?days=30"));
    p.appendChild(document.createTextNode(" devuelve "));
    p.appendChild(el("code", null, "total_impact_usd"));
    p.appendChild(document.createTextNode(", "));
    p.appendChild(el("code", null, "total_cost_usd"));
    p.appendChild(document.createTextNode(" y "));
    p.appendChild(el("code", null, "total_roi_percent"));
    p.appendChild(document.createTextNode("."));
    mr.appendChild(p);
    mr.appendChild(
      el(
        "div",
        "roi-formula",
        "ROI % = (total_impact_usd - total_cost_usd) / total_cost_usd × 100"
      )
    );
    mr.appendChild(
      el(
        "p",
        "process-note",
        "Este informe es análisis estático (sin USD reales). Para cost_llm: value ≈ cost_input + cost_output (tolerancia 0.01)."
      )
    );

    setupMetricsTabs();
  }}

  function setupMetricsTabs() {{
    const wrap = document.getElementById("metrics-tabs-wrap");
    if (!wrap || wrap.style.display === "none") return;
    const tabBtns = [
      document.getElementById("tab-btn-impact"),
      document.getElementById("tab-btn-cost"),
      document.getElementById("tab-btn-roi"),
    ];
    const panels = [
      document.getElementById("panel-impact"),
      document.getElementById("panel-cost"),
      document.getElementById("panel-roi"),
    ];
    function showTab(idx) {{
      panels.forEach((p, j) => {{
        if (!p) return;
        if (j === idx) p.removeAttribute("hidden");
        else p.setAttribute("hidden", "");
      }});
      tabBtns.forEach((b, j) => {{
        if (!b) return;
        const on = j === idx;
        b.setAttribute("aria-selected", on ? "true" : "false");
        b.classList.toggle("tab-btn-active", on);
        b.tabIndex = on ? 0 : -1;
      }});
    }}
    tabBtns.forEach((btn, i) => {{
      if (!btn) return;
      btn.addEventListener("click", () => showTab(i));
    }});
  }}

  function renderFinding(f, idx) {{
    const det = el("details", "finding");
    det.dataset.haystack = haystackForFinding(f);
    det.dataset.metrics = metricsFromFinding(f).join(",");

    const sum = el("summary");
    sum.appendChild(el("span", "fi-idx", idx + "."));
    sum.appendChild(el("code", null, f.file || ""));
    sum.appendChild(document.createTextNode(" — "));
    sum.appendChild(el("code", null, f.function || ""));
    const meta = el("span", "meta", " L" + (f.line != null ? f.line : "?") + " · " + (f.language || ""));
    sum.appendChild(meta);
    det.appendChild(sum);

    const body = el("div", "finding-body");

    if (f.llm) {{
      if (f.llm.ok) {{
        const p = el("p", "llm-ok");
        p.appendChild(el("strong", null, "LLM"));
        p.appendChild(document.createTextNode(" (agent_hint: "));
        p.appendChild(el("code", null, String(f.llm.agent_hint || "")));
        p.appendChild(document.createTextNode("): " + (f.llm.rationale || "")));
        body.appendChild(p);
      }} else {{
        body.appendChild(el("p", "llm-err", "LLM falló: " + (f.llm.error || "error")));
      }}
    }}

    const tbl = document.createElement("table");
    tbl.className = "sug";
    tbl.innerHTML = "<thead><tr><th>Categoría</th><th>Métrica</th><th>Razón</th><th>Sugerencia</th><th>Score</th></tr></thead><tbody></tbody>";
    const tb = tbl.querySelector("tbody");
    const sugs = f.suggestions || [];
    if (sugs.length === 0) {{
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 5;
      td.textContent = "Sin sugerencias";
      tr.appendChild(td);
      tb.appendChild(tr);
    }} else {{
      sugs.forEach((s) => {{
        const tr = document.createElement("tr");
        const cat = categoryForSuggestion(s);
        const td0 = document.createElement("td");
        td0.appendChild(el("code", null, cat || "—"));
        const td1 = document.createElement("td");
        td1.appendChild(el("code", null, s.metric || ""));
        const td2 = document.createElement("td");
        td2.textContent = s.reason || "";
        const td3 = document.createElement("td");
        td3.appendChild(el("code", null, suggestionText(s)));
        const td4 = document.createElement("td");
        td4.textContent = s.score != null ? String(s.score) : "";
        tr.appendChild(td0);
        tr.appendChild(td1);
        tr.appendChild(td2);
        tr.appendChild(td3);
        tr.appendChild(td4);
        tb.appendChild(tr);
      }});
    }}
    body.appendChild(tbl);
    det.appendChild(body);
    return det;
  }}

  function renderJsonValue(v, depth) {{
    if (v === null || typeof v !== "object") {{
      const s = el("span", "json-scalar", JSON.stringify(v));
      return s;
    }}
    if (Array.isArray(v)) {{
      const det = el("details", "json-node");
      if (depth < 2) det.open = true;
      const sm = el("summary", null, "[" + v.length + " items]");
      det.appendChild(sm);
      v.forEach((item, i) => {{
        const row = el("div", "json-row");
        row.appendChild(el("span", "json-k", String(i) + ": "));
        row.appendChild(renderJsonValue(item, depth + 1));
        det.appendChild(row);
      }});
      return det;
    }}
    const det = el("details", "json-node");
    if (depth < 2) det.open = true;
    const keys = Object.keys(v);
    det.appendChild(el("summary", null, "{{" + keys.length + " keys}}"));
    keys.forEach((k) => {{
      const row = el("div", "json-row");
      row.appendChild(el("span", "json-k", k + ": "));
      row.appendChild(renderJsonValue(v[k], depth + 1));
      det.appendChild(row);
    }});
    return det;
  }}

  function fillMetricFilter(findings) {{
    const sel = document.getElementById("metric-filter");
    const set = new Set();
    findings.forEach((f) => metricsFromFinding(f).forEach((m) => set.add(m)));
    [...set].sort().forEach((m) => {{
      const o = document.createElement("option");
      o.value = m;
      o.textContent = m;
      sel.appendChild(o);
    }});
  }}

  function updateCount() {{
    const all = document.querySelectorAll("#findings-root > details.finding");
    let vis = 0;
    all.forEach((d) => {{
      if (d.style.display !== "none") vis++;
    }});
    document.getElementById("count-badge").innerHTML =
      "Mostrando <strong>" + vis + "</strong> de <strong>" + all.length + "</strong> hallazgos";
  }}

  function applyFilter() {{
    const q = document.getElementById("search").value.trim().toLowerCase();
    const metric = document.getElementById("metric-filter").value;
    document.querySelectorAll("#findings-root > details.finding").forEach((det) => {{
      const hay = (det.dataset.haystack || "").toLowerCase();
      let show = !q || hay.includes(q);
      if (show && metric) {{
        const ms = (det.dataset.metrics || "").split(",").filter(Boolean);
        show = ms.includes(metric);
      }}
      det.style.display = show ? "" : "none";
    }});
    updateCount();
  }}

  let data;
  try {{
    data = decodePayload();
  }} catch (e) {{
    document.getElementById("mount-runtime").appendChild(
      el("p", "process-note", "No se pudo leer los datos embebidos: " + e)
    );
    return;
  }}

  const runId = (data.runtime && data.runtime.run_id) || "—";
  const sub = document.getElementById("header-sub");
  sub.textContent = "";
  sub.appendChild(document.createTextNode("Run "));
  const runCode = document.createElement("code");
  runCode.textContent = runId;
  sub.appendChild(runCode);
  sub.appendChild(document.createTextNode(" · vista interactiva · mismo contenido que zbills_report.json"));

  document.getElementById("mount-runtime").appendChild(buildRuntimeCard(data));
  const llm = buildLlmCard(data);
  if (llm) document.getElementById("mount-llm").appendChild(llm);

  const sumEl = document.getElementById("mount-summary");
  sumEl.replaceWith(buildSummaryCard(data));

  buildImpactCostRoi(data);

  const findings = data.findings || [];
  const root = document.getElementById("findings-root");
  findings.forEach((f, i) => root.appendChild(renderFinding(f, i + 1)));

  document.getElementById("json-pretty").textContent = JSON.stringify(data, null, 2);
  document.getElementById("json-tree").appendChild(renderJsonValue(data, 0));

  fillMetricFilter(findings);
  document.getElementById("toolbar").hidden = false;
  document.getElementById("search").addEventListener("input", applyFilter);
  document.getElementById("metric-filter").addEventListener("change", applyFilter);
  updateCount();

  document.getElementById("btn-expand").addEventListener("click", () => {{
    document.querySelectorAll("#findings-root > details.finding").forEach((d) => {{
      if (d.style.display !== "none") d.open = true;
    }});
  }});
  document.getElementById("btn-collapse").addEventListener("click", () => {{
    document.querySelectorAll("#findings-root > details.finding").forEach((d) => {{ d.open = false; }});
  }});
  document.getElementById("btn-copy-json").addEventListener("click", async () => {{
    const t = JSON.stringify(data, null, 2);
    try {{
      await navigator.clipboard.writeText(t);
      const b = document.getElementById("btn-copy-json");
      const prev = b.textContent;
      b.textContent = "Copiado";
      setTimeout(() => {{ b.textContent = prev; }}, 1600);
    }} catch (err) {{
      alert("No se pudo copiar. Selecciona el JSON en el panel de texto.");
    }}
  }});
}})();
  </script>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")
