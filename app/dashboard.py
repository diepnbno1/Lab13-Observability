from __future__ import annotations


def render_dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Day 13 Observability Dashboard</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f7f8fb;
      --surface: #ffffff;
      --ink: #152033;
      --muted: #667085;
      --line: #d9dee8;
      --blue: #2563eb;
      --teal: #0f766e;
      --rose: #e11d48;
      --amber: #b7791f;
      --green: #15803d;
      --violet: #6d28d9;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 28px 14px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
    }
    h1 {
      margin: 0;
      font-size: 22px;
      font-weight: 750;
    }
    .meta {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      box-shadow: 0 0 0 4px rgba(21, 128, 61, 0.12);
    }
    main {
      width: min(1440px, 100%);
      margin: 0 auto;
      padding: 22px 28px 32px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
    }
    .panel {
      min-height: 260px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      display: grid;
      grid-template-rows: auto auto minmax(120px, 1fr);
      gap: 10px;
    }
    .panel h2 {
      margin: 0;
      font-size: 15px;
      font-weight: 720;
    }
    .value {
      display: flex;
      align-items: baseline;
      gap: 8px;
      min-height: 34px;
    }
    .value strong {
      font-size: 28px;
      line-height: 1;
    }
    .value span {
      color: var(--muted);
      font-size: 13px;
    }
    canvas {
      width: 100%;
      height: 150px;
      display: block;
    }
    .breakdown {
      align-self: end;
      color: var(--muted);
      font-size: 12px;
      min-height: 18px;
    }
    @media (max-width: 1040px) {
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 720px) {
      header { align-items: flex-start; flex-direction: column; padding: 18px; }
      main { padding: 18px; }
      .grid { grid-template-columns: 1fr; }
      .meta { white-space: normal; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Day 13 Observability Dashboard</h1>
    <div class="meta"><span class="dot"></span><span id="updated">Waiting for metrics</span><span>Refresh 15s</span><span>Window 1h</span></div>
  </header>
  <main>
    <section class="grid" aria-label="Observability panels">
      <article class="panel"><h2>Latency P50 / P95 / P99</h2><div class="value"><strong id="latencyValue">0</strong><span>ms P95, SLO 3000ms</span></div><canvas id="latencyChart"></canvas><div class="breakdown" id="latencyBreakdown"></div></article>
      <article class="panel"><h2>Traffic</h2><div class="value"><strong id="trafficValue">0</strong><span>requests</span></div><canvas id="trafficChart"></canvas><div class="breakdown">Request count in current process</div></article>
      <article class="panel"><h2>Error Rate</h2><div class="value"><strong id="errorValue">0%</strong><span>SLO &lt; 2%</span></div><canvas id="errorChart"></canvas><div class="breakdown" id="errorBreakdown"></div></article>
      <article class="panel"><h2>Cost Over Time</h2><div class="value"><strong id="costValue">$0</strong><span>total, daily budget $2.50</span></div><canvas id="costChart"></canvas><div class="breakdown" id="costBreakdown"></div></article>
      <article class="panel"><h2>Tokens In / Out</h2><div class="value"><strong id="tokenValue">0</strong><span>tokens total</span></div><canvas id="tokenChart"></canvas><div class="breakdown" id="tokenBreakdown"></div></article>
      <article class="panel"><h2>Quality Proxy</h2><div class="value"><strong id="qualityValue">0.00</strong><span>SLO &gt;= 0.75</span></div><canvas id="qualityChart"></canvas><div class="breakdown">Heuristic quality score average</div></article>
    </section>
  </main>
  <script>
    const colors = {
      latency: "#2563eb",
      traffic: "#0f766e",
      error: "#e11d48",
      cost: "#b7791f",
      tokensIn: "#6d28d9",
      tokensOut: "#15803d",
      quality: "#0f766e",
      threshold: "#94a3b8"
    };

    function fmtTime(value) {
      return new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    }

    function setText(id, value) {
      document.getElementById(id).textContent = value;
    }

    function drawLine(canvasId, values, color, threshold) {
      const canvas = document.getElementById(canvasId);
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(320, Math.floor(rect.width * window.devicePixelRatio));
      canvas.height = Math.floor(150 * window.devicePixelRatio);
      const ctx = canvas.getContext("2d");
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);
      ctx.strokeStyle = "#d9dee8";
      ctx.lineWidth = 1 * window.devicePixelRatio;
      ctx.beginPath();
      ctx.moveTo(0, h - 1);
      ctx.lineTo(w, h - 1);
      ctx.stroke();
      const nums = values.map(Number).filter(Number.isFinite);
      const max = Math.max(1, threshold || 0, ...nums);
      if (threshold) {
        const y = h - (threshold / max) * (h - 18) - 8;
        ctx.strokeStyle = colors.threshold;
        ctx.setLineDash([6 * window.devicePixelRatio, 5 * window.devicePixelRatio]);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
        ctx.setLineDash([]);
      }
      if (nums.length === 0) return;
      ctx.strokeStyle = color;
      ctx.lineWidth = 2 * window.devicePixelRatio;
      ctx.beginPath();
      nums.forEach((value, index) => {
        const x = nums.length === 1 ? w : (index / (nums.length - 1)) * w;
        const y = h - (value / max) * (h - 18) - 8;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.stroke();
    }

    function drawBars(canvasId, leftValues, rightValues) {
      const canvas = document.getElementById(canvasId);
      const rect = canvas.getBoundingClientRect();
      canvas.width = Math.max(320, Math.floor(rect.width * window.devicePixelRatio));
      canvas.height = Math.floor(150 * window.devicePixelRatio);
      const ctx = canvas.getContext("2d");
      const w = canvas.width;
      const h = canvas.height;
      const left = leftValues.map(Number);
      const right = rightValues.map(Number);
      const max = Math.max(1, ...left, ...right);
      ctx.clearRect(0, 0, w, h);
      const count = Math.max(left.length, right.length, 1);
      const slot = w / count;
      for (let i = 0; i < count; i += 1) {
        const x = i * slot + slot * 0.18;
        const bw = Math.max(3, slot * 0.24);
        const lh = ((left[i] || 0) / max) * (h - 16);
        const rh = ((right[i] || 0) / max) * (h - 16);
        ctx.fillStyle = colors.tokensIn;
        ctx.fillRect(x, h - lh, bw, lh);
        ctx.fillStyle = colors.tokensOut;
        ctx.fillRect(x + bw + 3, h - rh, bw, rh);
      }
    }

    function cumulative(values) {
      let total = 0;
      return values.map((value) => {
        total += Number(value) || 0;
        return total;
      });
    }

    async function refresh() {
      const response = await fetch("/dashboard/data", { cache: "no-store" });
      const payload = await response.json();
      const s = payload.snapshot;
      const series = payload.series;
      setText("updated", `Updated ${fmtTime(payload.generated_at)}`);
      setText("latencyValue", `${s.latency_p95}`);
      setText("latencyBreakdown", `P50 ${s.latency_p50}ms · P95 ${s.latency_p95}ms · P99 ${s.latency_p99}ms`);
      setText("trafficValue", String(s.traffic));
      setText("errorValue", `${s.error_rate_pct}%`);
      setText("errorBreakdown", Object.keys(s.error_breakdown).length ? JSON.stringify(s.error_breakdown) : "No errors recorded");
      setText("costValue", `$${s.total_cost_usd.toFixed(6)}`);
      setText("costBreakdown", `Average $${s.avg_cost_usd.toFixed(6)} per request`);
      setText("tokenValue", String(s.tokens_in_total + s.tokens_out_total));
      setText("tokenBreakdown", `In ${s.tokens_in_total} · Out ${s.tokens_out_total}`);
      setText("qualityValue", s.quality_avg.toFixed(2));
      drawLine("latencyChart", series.map((x) => x.latency_ms), colors.latency, payload.slo.latency_p95_ms);
      drawLine("trafficChart", cumulative(series.map(() => 1)), colors.traffic);
      drawLine("errorChart", payload.errors.map(() => 1), colors.error, 1);
      drawLine("costChart", cumulative(series.map((x) => x.cost_usd)), colors.cost, payload.slo.daily_cost_usd);
      drawBars("tokenChart", series.map((x) => x.tokens_in), series.map((x) => x.tokens_out));
      drawLine("qualityChart", series.map((x) => x.quality_score), colors.quality, payload.slo.quality_score_avg);
    }

    refresh();
    setInterval(refresh, 15000);
    window.addEventListener("resize", refresh);
  </script>
</body>
</html>"""
