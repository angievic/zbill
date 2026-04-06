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

  function haystackForFinding(f) {{
    const parts = [f.file, f.function, f.language, String(f.line)];
    (f.suggestions || []).forEach((s) => {{
      parts.push(s.metric, s.reason, s.example);
    }});
    if (f.llm) parts.push(JSON.stringify(f.llm));
    return parts.join("\\n");
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
    tbl.innerHTML = "<thead><tr><th>Métrica</th><th>Razón</th><th>Ejemplo</th><th>Score</th></tr></thead><tbody></tbody>";
    const tb = tbl.querySelector("tbody");
    const sugs = f.suggestions || [];
    if (sugs.length === 0) {{
      const tr = document.createElement("tr");
      const td = document.createElement("td");
      td.colSpan = 4;
      td.textContent = "Sin sugerencias";
      tr.appendChild(td);
      tb.appendChild(tr);
    }} else {{
      sugs.forEach((s) => {{
        const tr = document.createElement("tr");
        const td1 = document.createElement("td");
        td1.appendChild(el("code", null, s.metric || ""));
        const td2 = document.createElement("td");
        td2.textContent = s.reason || "";
        const td3 = document.createElement("td");
        td3.appendChild(el("code", null, s.example || ""));
        const td4 = document.createElement("td");
        td4.textContent = s.score != null ? String(s.score) : "";
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
