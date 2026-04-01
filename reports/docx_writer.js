#!/usr/bin/env node
/**
 * eth_forensic_report.js
 * ──────────────────────
 * Reads all eth_report_*.json and trace_*.json files from the
 * reports/ and traces/ directories, aggregates them chronologically,
 * and produces a single forensic-grade .docx report.
 *
 * USAGE:   node eth_forensic_report.js [--dir /path/to/root]
 * OUTPUT:  forensic_report_TIMESTAMP.docx
 * DEPS:    npm install -g docx
 */

const fs   = require("fs");
const path = require("path");

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageBreak, LevelFormat,
  TabStopType, TabStopPosition,
} = require("docx");

// ── Config ───────────────────────────────────────────────────────────────────

const args    = process.argv.slice(2);
const dirArg  = args.indexOf("--dir");
const ROOT    = dirArg >= 0 ? args[dirArg + 1] : path.join(__dirname, "..");
const REP_DIR = path.join(ROOT, "data", "reports");
const TRC_DIR = path.join(ROOT, "data", "traces");
const OUT_DIR = path.join(ROOT, "data", "reports");

const NOW     = new Date();
const TS_SLUG = NOW.toISOString().replace(/[:.]/g, "-").slice(0, 19);

// ── Colours ──────────────────────────────────────────────────────────────────
const C = {
  black:      "000000",
  darkBlue:   "1A2C5B",
  midBlue:    "2E5FA3",
  lightBlue:  "D6E4F7",
  red:        "C0392B",
  orange:     "E67E22",
  darkGrey:   "444444",
  midGrey:    "888888",
  lightGrey:  "F2F2F2",
  white:      "FFFFFF",
  amber:      "F39C12",
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function loadJSON(fp) {
  try { return JSON.parse(fs.readFileSync(fp, "utf8")); }
  catch (e) { console.warn(`Skipping ${fp}: ${e.message}`); return null; }
}

function fmtUSD(n) {
  if (!n) return "$0.00";
  return "$" + Number(n).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function fmtETH(n) {
  if (!n) return "0.0000 ETH";
  return Number(n).toFixed(4) + " ETH";
}

function fmtDate(iso) {
  if (!iso) return "Unknown";
  return new Date(iso).toUTCString().replace(" GMT", " UTC");
}

function fmtDateShort(iso) {
  if (!iso) return "Unknown";
  return new Date(iso).toISOString().slice(0, 10);
}

function blank(n = 1) {
  return Array.from({ length: n }, () =>
    new Paragraph({ children: [new TextRun("")], spacing: { after: 0 } })
  );
}

// ── Typography helpers ────────────────────────────────────────────────────────

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, color: C.darkBlue, bold: true, size: 36 })],
    spacing: { before: 360, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: C.midBlue, space: 4 } },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, color: C.midBlue, bold: true, size: 28 })],
    spacing: { before: 280, after: 80 },
  });
}

function h3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [new TextRun({ text, color: C.darkGrey, bold: true, size: 24 })],
    spacing: { before: 200, after: 60 },
  });
}

function para(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({
      text,
      size: opts.size || 22,
      color: opts.color || C.black,
      bold: opts.bold || false,
      italics: opts.italic || false,
      font: "Arial",
    })],
    spacing: { after: opts.after !== undefined ? opts.after : 120 },
    alignment: opts.align || AlignmentType.LEFT,
  });
}

function mono(text, color) {
  return new Paragraph({
    children: [new TextRun({
      text,
      size: 18,
      color: color || C.darkGrey,
      font: "Courier New",
    })],
    spacing: { after: 60 },
    indent: { left: 720 },
  });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun({
      text,
      size: opts.size || 22,
      color: opts.color || C.black,
      bold: opts.bold || false,
      font: "Arial",
    })],
    spacing: { after: 80 },
  });
}

function labelValue(label, value, highlight) {
  return new Paragraph({
    children: [
      new TextRun({ text: label + ": ", bold: true, size: 22, font: "Arial", color: C.darkGrey }),
      new TextRun({ text: value, size: 22, font: "Arial", color: highlight || C.black }),
    ],
    spacing: { after: 80 },
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function divider() {
  return new Paragraph({
    children: [new TextRun("")],
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.lightBlue, space: 2 } },
    spacing: { after: 120 },
  });
}

function alertBox(text, severity) {
  const fill = severity === "HIGH" ? "FDECEA" : severity === "MED" ? "FEF9E7" : "EAF4FB";
  const bc   = severity === "HIGH" ? C.red    : severity === "MED" ? C.amber  : C.midBlue;
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({ children: [
      new TableCell({
        width: { size: 9360, type: WidthType.DXA },
        shading: { fill, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 200, right: 200 },
        borders: {
          top:    { style: BorderStyle.SINGLE, size: 6, color: bc },
          bottom: { style: BorderStyle.SINGLE, size: 6, color: bc },
          left:   { style: BorderStyle.THICK,  size: 16, color: bc },
          right:  { style: BorderStyle.SINGLE, size: 6, color: bc },
        },
        children: [new Paragraph({ children: [new TextRun({ text, size: 22, font: "Arial", color: C.black })] })],
      })
    ]})]
  });
}

function txTable(rows) {
  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const headerShade = { fill: C.darkBlue, type: ShadingType.CLEAR };
  const altShade    = { fill: C.lightGrey, type: ShadingType.CLEAR };

  const colWidths = [1400, 1800, 1600, 4560]; // Date | Amount | Token | TX Hash
  const total = colWidths.reduce((a, b) => a + b, 0);

  function hdrCell(text, w) {
    return new TableCell({
      width: { size: w, type: WidthType.DXA },
      shading: headerShade,
      borders,
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text, size: 18, bold: true, color: C.white, font: "Arial" })] })],
    });
  }

  function dataCell(text, w, color, mono) {
    return new TableCell({
      width: { size: w, type: WidthType.DXA },
      borders,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text, size: mono ? 16 : 18, color: color || C.black, font: mono ? "Courier New" : "Arial" })] })],
    });
  }

  const tableRows = [
    new TableRow({ children: [
      hdrCell("Date (UTC)", colWidths[0]),
      hdrCell("Amount", colWidths[1]),
      hdrCell("Token", colWidths[2]),
      hdrCell("TX Hash", colWidths[3]),
    ]}),
    ...rows.map((r, i) => {
      const shade = i % 2 === 1 ? altShade : undefined;
      return new TableRow({ children: [
        new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: r.date, size: 18, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: r.amount, size: 18, bold: true, font: "Arial", color: C.red })] })] }),
        new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: r.token, size: 18, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[3], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: r.hash, size: 15, font: "Courier New", color: C.midBlue })] })] }),
      ]});
    }),
  ];

  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: colWidths, rows: tableRows });
}

// ── Load all data ─────────────────────────────────────────────────────────────

function loadAllReports() {
  if (!fs.existsSync(REP_DIR)) return [];
  return fs.readdirSync(REP_DIR)
    .filter(f => f.match(/^eth_report_\d{8}_\d{6}\.json$/))
    .sort()
    .map(f => ({ file: f, data: loadJSON(path.join(REP_DIR, f)) }))
    .filter(r => r.data);
}

function loadAllTraces() {
  if (!fs.existsSync(TRC_DIR)) return [];
  return fs.readdirSync(TRC_DIR)
    .filter(f => f.match(/^trace_.*\.json$/))
    .sort()
    .map(f => ({ file: f, data: loadJSON(path.join(TRC_DIR, f)) }))
    .filter(t => t.data);
}

// ── Aggregate across all reports ──────────────────────────────────────────────

function aggregate(reports) {
  const walletHistory = {};  // address -> array of per-report snapshots
  let totalSpikes     = 0;
  let allSpikes       = [];
  let allInternal     = [];

  for (const { file, data } of reports) {
    const ep = data.eth_spot_usd || 0;
    totalSpikes += data.batch_totals?.spike_count || 0;
    allSpikes   = allSpikes.concat((data.spikes || []).map(s => ({ ...s, report: file, eth_price: ep })));

    for (const w of (data.wallets || [])) {
      const addr = w.address.toLowerCase();
      if (!walletHistory[addr]) walletHistory[addr] = { label: w.label, address: w.address, snapshots: [] };
      walletHistory[addr].snapshots.push({ ...w, report_date: data.generated_at, eth_price: ep });
    }

    // Internal movements — spikes where sender is a known wallet
    const knownAddrs = new Set((data.wallets || []).map(w => w.address.toLowerCase()));
    for (const s of (data.spikes || [])) {
      if (knownAddrs.has(s.from.toLowerCase())) {
        allInternal.push({ ...s, report: file, eth_price: ep });
      }
    }
  }

  return { walletHistory, totalSpikes, allSpikes, allInternal };
}

// ── Build document sections ───────────────────────────────────────────────────

function buildCover(reports) {
  const first = reports[0]?.data;
  const last  = reports[reports.length - 1]?.data;
  const from  = first?.window_from  || "Unknown";
  const to    = last?.generated_at  || "Unknown";

  return [
    ...blank(6),
    new Paragraph({
      children: [new TextRun({ text: "BLOCKCHAIN FORENSIC ANALYSIS REPORT", size: 56, bold: true, color: C.darkBlue, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    }),
    new Paragraph({
      children: [new TextRun({ text: "BDAG Investigation — ChainSentinel", size: 36, color: C.midBlue, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
    }),
    new Paragraph({
      border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: C.midBlue } },
      children: [new TextRun("")],
      spacing: { after: 200 },
    }),
    ...blank(1),
    new Paragraph({
      children: [new TextRun({ text: "Investigation Period", size: 28, bold: true, color: C.darkGrey, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 80 },
    }),
    new Paragraph({
      children: [new TextRun({ text: fmtDate(from), size: 26, color: C.black, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
    }),
    new Paragraph({
      children: [new TextRun({ text: "to", size: 22, color: C.midGrey, font: "Arial", italics: true })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
    }),
    new Paragraph({
      children: [new TextRun({ text: fmtDate(to), size: 26, color: C.black, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
    }),
    ...blank(1),
    new Paragraph({
      children: [new TextRun({ text: `Report Generated: ${fmtDate(NOW.toISOString())}`, size: 22, color: C.midGrey, font: "Arial", italics: true })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
    }),
    new Paragraph({
      children: [new TextRun({ text: `Reports Analysed: ${reports.length}`, size: 22, color: C.midGrey, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
    }),
    new Paragraph({
      children: [new TextRun({ text: "CONFIDENTIAL — FOR ATTORNEY USE ONLY", size: 22, bold: true, color: C.red, font: "Arial" })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 60 },
    }),
    pageBreak(),
  ];
}

function buildExecutiveSummary(reports, agg, traces) {
  const first = reports[0]?.data;
  const last  = reports[reports.length - 1]?.data;
  const bt    = last?.batch_totals || {};
  const totalIn  = reports.reduce((s, r) => s + (r.data.batch_totals?.total_in_usd || 0), 0);
  const totalOut = reports.reduce((s, r) => s + (r.data.batch_totals?.total_out_usd || 0), 0);
  const activeWallets = new Set(agg.allSpikes.map(s => s.wallet)).size;
  const exchangeHits = traces.filter(t => t.data.narrative?.exchange_detected).length;
  const mixerHits    = traces.filter(t => t.data.narrative?.mixer_detected).length;

  const items = [
    h1("1. Executive Summary"),
    para(
      `This report documents blockchain forensic analysis conducted on ${reports.length} monitoring ` +
      `cycle${reports.length !== 1 ? "s" : ""} spanning the period from ${fmtDateShort(first?.window_from)} ` +
      `to ${fmtDateShort(last?.generated_at)}. The investigation tracked ${last?.wallets?.length || 0} ` +
      `Ethereum wallet addresses associated with the BDAG scheme across ETH and USDT transactions.`
    ),
    ...blank(1),
    h2("Key Findings"),
    bullet(`Total inbound volume across all monitored wallets: ${fmtUSD(totalIn)}`),
    bullet(`Total outbound volume: ${fmtUSD(totalOut)}`),
    bullet(`Net flow (in minus out): ${fmtUSD(totalIn - totalOut)} — ${totalIn > totalOut ? "wallets are accumulating funds" : "funds are being distributed"}`),
    bullet(`${agg.totalSpikes} high-value transactions detected exceeding $50,000 USD each`),
    bullet(`${activeWallets} distinct wallet addresses recorded large inbound transfers`),
    bullet(`${traces.length} hop trace${traces.length !== 1 ? "s" : ""} conducted on flagged wallets`),
    exchangeHits > 0 ? bullet(`${exchangeHits} trace(s) terminated at identified exchange hot wallets`) : null,
    mixerHits > 0    ? bullet(`${mixerHits} trace(s) identified Tornado Cash or mixing service involvement — strong laundering indicator`, { color: C.red, bold: true }) : null,
    agg.allInternal.length > 0 ? bullet(`${agg.allInternal.length} internal transfers detected between tracked wallets — consistent with layering activity`) : null,
  ].filter(Boolean);

  if (mixerHits > 0) {
    items.push(...blank(1));
    items.push(alertBox(
      `WARNING: ${mixerHits} trace(s) identified Tornado Cash mixer involvement. ` +
      `The deliberate use of mixing services to obscure the origin of funds is a recognised indicator of money laundering ` +
      `under FATF guidance and relevant AML frameworks.`,
      "HIGH"
    ));
  }

  if (agg.allInternal.length > 0) {
    items.push(...blank(1));
    items.push(alertBox(
      `NOTE: ${agg.allInternal.length} transactions were identified as transfers between wallets ` +
      `already tracked in this investigation. This pattern — moving funds between controlled addresses — ` +
      `is consistent with the layering stage of money laundering.`,
      "MED"
    ));
  }

  items.push(pageBreak());
  return items;
}

function buildTimeline(reports) {
  const items = [h1("2. Activity Timeline")];
  items.push(para(
    "The following table presents a chronological overview of monitoring cycles conducted during the investigation period. " +
    "Each row represents a 48-hour monitoring window with aggregate activity across all tracked wallets."
  ));
  items.push(...blank(1));

  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const colWidths = [1800, 1800, 2200, 2200, 1360];

  function hCell(text, w) {
    return new TableCell({
      width: { size: w, type: WidthType.DXA }, borders,
      shading: { fill: C.darkBlue, type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text, size: 18, bold: true, color: C.white, font: "Arial" })] })],
    });
  }
  function dCell(text, w, color, isMono) {
    return new TableCell({
      width: { size: w, type: WidthType.DXA }, borders,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({ children: [new TextRun({ text, size: isMono ? 16 : 18, color: color || C.black, font: isMono ? "Courier New" : "Arial" })] })],
    });
  }

  const rows = [
    new TableRow({ children: [
      hCell("Report Date", colWidths[0]),
      hCell("Window Start", colWidths[1]),
      hCell("Total IN", colWidths[2]),
      hCell("Total OUT", colWidths[3]),
      hCell("Spikes", colWidths[4]),
    ]}),
    ...reports.map((r, i) => {
      const d  = r.data;
      const bt = d.batch_totals || {};
      const shade = i % 2 === 1 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined;
      return new TableRow({ children: [
        new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: fmtDateShort(d.generated_at), size: 18, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: fmtDateShort(d.window_from), size: 18, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: fmtUSD(bt.total_in_usd), size: 18, bold: true, color: C.red, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[3], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: fmtUSD(bt.total_out_usd), size: 18, font: "Arial" })] })] }),
        new TableCell({ width: { size: colWidths[4], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
          children: [new Paragraph({ children: [new TextRun({ text: String(bt.spike_count || 0), size: 18, bold: (bt.spike_count || 0) > 0, color: (bt.spike_count || 0) > 0 ? C.red : C.black, font: "Arial" })] })] }),
      ]});
    }),
  ];

  items.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows }));
  items.push(pageBreak());
  return items;
}

function buildWalletProfiles(agg, reports) {
  const items = [h1("3. Wallet Profiles")];
  items.push(para(
    "This section provides a forensic profile of each wallet that recorded activity during the investigation period. " +
    "Profiles include cumulative volume across all monitoring cycles, transaction counts, and spike activity."
  ));

  // Aggregate per wallet across all reports
  const wallets = Object.values(agg.walletHistory)
    .map(w => {
      const active = w.snapshots.filter(s => s.total_in_usd > 0 || s.total_out_usd > 0);
      if (!active.length) return null;
      return {
        label:        w.label,
        address:      w.address,
        total_in:     active.reduce((s, r) => s + (r.total_in_usd || 0), 0),
        total_out:    active.reduce((s, r) => s + (r.total_out_usd || 0), 0),
        eth_in:       active.reduce((s, r) => s + (r.eth_in || 0), 0),
        eth_out:      active.reduce((s, r) => s + (r.eth_out || 0), 0),
        usdt_in:      active.reduce((s, r) => s + (r.usdt_in || 0), 0),
        usdt_out:     active.reduce((s, r) => s + (r.usdt_out || 0), 0),
        spike_count:  active.reduce((s, r) => s + (r.spike_count || 0), 0),
        tx_count:     active.reduce((s, r) => s + (r.tx_count_normal || 0) + (r.tx_count_usdt || 0), 0),
        active_periods: active.length,
        first_seen:   active[0]?.report_date,
        last_seen:    active[active.length - 1]?.report_date,
        spikes:       agg.allSpikes.filter(s => s.wallet?.toLowerCase() === w.address.toLowerCase()),
        ep:           active[active.length - 1]?.eth_price || 0,
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.total_in - a.total_in);

  for (const [i, w] of wallets.entries()) {
    items.push(h2(`3.${i + 1}  ${w.label}`));
    items.push(labelValue("Address", w.address));
    items.push(labelValue("First Active", fmtDate(w.first_seen)));
    items.push(labelValue("Last Active", fmtDate(w.last_seen)));
    items.push(labelValue("Active Monitoring Cycles", String(w.active_periods)));
    items.push(labelValue("Total Transactions", String(w.tx_count)));
    items.push(...blank(1));

    // Volume summary table
    const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
    const borders = { top: border, bottom: border, left: border, right: border };
    const volRows = [
      ["Metric", "Amount"],
      ["Total Inbound (USD)",  fmtUSD(w.total_in)],
      ["Total Outbound (USD)", fmtUSD(w.total_out)],
      ["Net Flow (USD)",       fmtUSD(w.total_in - w.total_out)],
      ["ETH Received",         fmtETH(w.eth_in) + `  (${fmtUSD(w.eth_in * w.ep)})`],
      ["ETH Sent",             fmtETH(w.eth_out) + `  (${fmtUSD(w.eth_out * w.ep)})`],
      ["USDT Received",        fmtUSD(w.usdt_in)],
      ["USDT Sent",            fmtUSD(w.usdt_out)],
      ["Large Tx Alerts (>$50k)", String(w.spike_count)],
    ];

    const tbl = new Table({
      width: { size: 6000, type: WidthType.DXA },
      columnWidths: [3000, 3000],
      rows: volRows.map((row, ri) => new TableRow({ children: row.map((cell, ci) => new TableCell({
        width: { size: 3000, type: WidthType.DXA }, borders,
        shading: ri === 0 ? { fill: C.midBlue, type: ShadingType.CLEAR } : ci === 0 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined,
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        children: [new Paragraph({ children: [new TextRun({
          text: cell,
          size: 20,
          bold: ri === 0 || ci === 0,
          color: ri === 0 ? C.white : (ci === 1 && ri === 3) ? (w.total_in > w.total_out ? C.red : C.darkBlue) : C.black,
          font: "Arial",
        })] })],
      }))})),
    });
    items.push(tbl);

    // Spike detail
    if (w.spikes.length > 0) {
      items.push(...blank(1));
      items.push(h3(`Large Inbound Transactions (${w.spikes.length} alert${w.spikes.length !== 1 ? "s" : ""})`));
      items.push(alertBox(
        `This wallet triggered ${w.spikes.length} large inbound transaction alert(s) during the monitoring period. ` +
        `Each transaction below exceeded the $50,000 USD threshold and is detailed for evidentiary purposes.`,
        w.spikes.length > 5 ? "HIGH" : "MED"
      ));
      items.push(...blank(1));

      const rows = w.spikes
        .sort((a, b) => b.amount_usd - a.amount_usd)
        .map(s => {
          const dt = new Date(s.timestamp * 1000).toISOString().slice(0, 16).replace("T", " ") + " UTC";
          const amt = s.token === "ETH"
            ? `${fmtETH(s.amount_eth)} (${fmtUSD(s.amount_usd)})`
            : fmtUSD(s.amount_usd);
          return { date: dt, amount: amt, token: s.token, hash: s.hash };
        });

      items.push(txTable(rows));
      items.push(...blank(1));
      items.push(h3("Sender Addresses"));
      const senders = [...new Set(w.spikes.map(s => s.from))];
      for (const sender of senders) {
        const txsFromSender = w.spikes.filter(s => s.from === sender);
        items.push(new Paragraph({
          children: [
            new TextRun({ text: sender, size: 18, font: "Courier New", color: C.midBlue }),
            new TextRun({ text: `  —  ${txsFromSender.length} tx(s), total ${fmtUSD(txsFromSender.reduce((s, t) => s + t.amount_usd, 0))}`, size: 18, font: "Arial", color: C.darkGrey }),
          ],
          spacing: { after: 80 },
        }));
      }
    }

    items.push(divider());
  }

  items.push(pageBreak());
  return items;
}

function buildTraceSection(traces) {
  const items = [h1("4. Hop Trace Analysis")];
  items.push(para(
    "When a wallet was flagged for large inbound transactions, a hop trace was conducted to identify the ultimate source of funds. " +
    "Each trace follows the chain of inbound transfers backwards through up to 7 hops, identifying exchanges, mixers, and intermediate wallets."
  ));

  if (traces.length === 0) {
    items.push(...blank(1));
    items.push(para("No hop traces have been conducted. Run eth_trace.py on flagged wallets to populate this section.", { italic: true, color: C.midGrey }));
    items.push(pageBreak());
    return items;
  }

  for (const [i, { file, data }] of traces.entries()) {
    const narr  = data.narrative || {};
    const hops  = data.hops || [];
    const target = hops[0] || {};

    items.push(h2(`4.${i + 1}  ${data.target_label || "Unknown Wallet"}`));
    items.push(labelValue("Target Address", data.target_address || "Unknown"));
    items.push(labelValue("Trace Conducted", fmtDate(data.traced_at)));
    items.push(labelValue("Hops Traced", String(narr.hops_traced || hops.length - 1)));
    items.push(labelValue("Source File", file));
    items.push(...blank(1));

    // Status flags
    if (narr.mixer_detected) {
      items.push(alertBox("MIXER DETECTED — Tornado Cash or mixing service identified in this trace chain. Funds were deliberately obfuscated before reaching the target wallet. This is a strong indicator of intentional money laundering.", "HIGH"));
      items.push(...blank(1));
    }
    if (narr.exchange_detected) {
      const names = (narr.exchange_names || []).filter(Boolean).join(", ");
      items.push(alertBox(`EXCHANGE IDENTIFIED — ${names || "Known exchange hot wallet"} detected in this trace chain. Funds originated from or passed through a centralised exchange.`, "MED"));
      items.push(...blank(1));
    }
    if (narr.known_wallets_in_chain > 0) {
      items.push(alertBox(`INTERNAL MOVEMENT — ${narr.known_wallets_in_chain} wallet(s) in this trace chain are already tracked in the master wallet list. This confirms internal fund cycling between controlled addresses.`, "MED"));
      items.push(...blank(1));
    }

    // Hop chain table
    if (hops.length > 0) {
      items.push(h3("Hop Chain"));
      const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
      const borders = { top: border, bottom: border, left: border, right: border };
      const colWidths = [600, 3200, 2200, 1200, 2160];

      const hopRows = [
        new TableRow({ children: [
          new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: "Hop", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
          new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: "Address", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
          new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: "Classification", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
          new TableCell({ width: { size: colWidths[3], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: "TX Count", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
          new TableCell({ width: { size: colWidths[4], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
            children: [new Paragraph({ children: [new TextRun({ text: "ETH Balance", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
        ]}),
        ...hops.map((hop, hi) => {
          const c = hop.classification;
          const shade = hi % 2 === 1 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined;
          const classColor = c === "MIXER" ? C.red : c === "KNOWN_EXCHANGE" || c === "LIKELY_EXCHANGE" ? C.orange : c === "ORIGIN" ? C.midBlue : C.black;
          const classLabel = hop.exchange_label || hop.known_label || c;
          const hopLabel = hop.hop === 0 ? "TARGET" : `HOP ${hop.hop}`;
          return new TableRow({ children: [
            new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
              children: [new Paragraph({ children: [new TextRun({ text: hopLabel, size: 18, bold: hop.hop === 0, font: "Arial" })] })] }),
            new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
              children: [new Paragraph({ children: [new TextRun({ text: hop.address, size: 15, font: "Courier New", color: C.midBlue })] })] }),
            new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
              children: [new Paragraph({ children: [new TextRun({ text: classLabel || c, size: 18, bold: c === "MIXER", color: classColor, font: "Arial" })] })] }),
            new TableCell({ width: { size: colWidths[3], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
              children: [new Paragraph({ children: [new TextRun({ text: String(hop.tx_count || 0), size: 18, font: "Arial" })] })] }),
            new TableCell({ width: { size: colWidths[4], type: WidthType.DXA }, borders, shading: shade, margins: { top: 60, bottom: 60, left: 100, right: 100 },
              children: [new Paragraph({ children: [new TextRun({ text: fmtETH(hop.eth_balance), size: 18, font: "Arial" })] })] }),
          ]});
        }),
      ];

      items.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows: hopRows }));
    }

    // Narrative text
    if (narr.text) {
      items.push(...blank(1));
      items.push(h3("Trace Narrative"));
      for (const line of narr.text.split("\n")) {
        if (!line.trim()) continue;
        items.push(new Paragraph({
          children: [new TextRun({ text: line, size: 20, font: "Arial", color: line.startsWith("***") ? C.red : C.darkGrey })],
          spacing: { after: 60 },
          indent: { left: line.startsWith("  ") ? 720 : 0 },
        }));
      }
    }

    items.push(divider());
  }

  items.push(pageBreak());
  return items;
}

function buildInternalMovements(agg) {
  const items = [h1("5. Internal Fund Movements")];
  items.push(para(
    "Internal movements are transactions where the sender address is itself a tracked wallet in the master list. " +
    "This pattern — transferring funds between controlled addresses — is consistent with the layering stage of money laundering, " +
    "designed to obscure the audit trail between the source of funds and the ultimate beneficiary."
  ));
  items.push(...blank(1));

  if (agg.allInternal.length === 0) {
    items.push(para("No internal movements detected across the monitoring period.", { italic: true, color: C.midGrey }));
    items.push(pageBreak());
    return items;
  }

  items.push(alertBox(
    `${agg.allInternal.length} internal transfer(s) detected totalling ${fmtUSD(agg.allInternal.reduce((s, m) => s + m.amount_usd, 0))} USD. ` +
    `Each transaction below represents a transfer between two wallets both tracked in this investigation.`,
    "MED"
  ));
  items.push(...blank(1));

  const knownMap = {};
  for (const snap of Object.values(agg.walletHistory)) {
    knownMap[snap.address.toLowerCase()] = snap.label;
  }

  for (const mv of agg.allInternal.sort((a, b) => b.amount_usd - a.amount_usd)) {
    const fromLabel = knownMap[mv.from.toLowerCase()] || "Unknown";
    const toLabel   = mv.wallet_label || knownMap[mv.wallet?.toLowerCase()] || "Unknown";
    const dt = new Date(mv.timestamp * 1000).toISOString().slice(0, 16).replace("T", " ") + " UTC";
    const amt = mv.token === "ETH"
      ? `${fmtETH(mv.amount_eth)} (${fmtUSD(mv.amount_usd)})`
      : fmtUSD(mv.amount_usd);

    items.push(new Paragraph({
      children: [
        new TextRun({ text: fromLabel, bold: true, size: 22, color: C.red, font: "Arial" }),
        new TextRun({ text: "   →   ", size: 22, font: "Arial", color: C.midGrey }),
        new TextRun({ text: toLabel,   bold: true, size: 22, color: C.darkBlue, font: "Arial" }),
      ],
      spacing: { after: 60 },
    }));
    items.push(labelValue("Amount",   amt));
    items.push(labelValue("Date",     dt));
    items.push(labelValue("From",     mv.from));
    items.push(labelValue("To",       mv.wallet || ""));
    items.push(labelValue("TX Hash",  mv.hash));
    items.push(labelValue("Report",   mv.report || ""));
    items.push(divider());
  }

  items.push(pageBreak());
  return items;
}

function buildConclusions(reports, agg, traces) {
  const totalIn     = reports.reduce((s, r) => s + (r.data.batch_totals?.total_in_usd || 0), 0);
  const totalOut    = reports.reduce((s, r) => s + (r.data.batch_totals?.total_out_usd || 0), 0);
  const mixerTraces = traces.filter(t => t.data.narrative?.mixer_detected);
  const exchTraces  = traces.filter(t => t.data.narrative?.exchange_detected);
  const first       = reports[0]?.data;
  const last        = reports[reports.length - 1]?.data;

  const items = [h1("6. Conclusions & Observations")];
  items.push(para(
    `Based on blockchain forensic analysis of ${reports.length} monitoring cycle(s) conducted between ` +
    `${fmtDateShort(first?.window_from)} and ${fmtDateShort(last?.generated_at)}, the following conclusions are drawn:`
  ));
  items.push(...blank(1));

  items.push(h2("Volume & Flow Analysis"));
  items.push(para(
    `The tracked wallet network received a cumulative total of ${fmtUSD(totalIn)} and disbursed ${fmtUSD(totalOut)} during the investigation window. ` +
    `The net flow of ${fmtUSD(Math.abs(totalIn - totalOut))} indicates the network is ${totalIn > totalOut ? "accumulating" : "distributing"} funds. ` +
    `A total of ${agg.totalSpikes} individual transactions exceeded the $50,000 USD alert threshold.`
  ));

  items.push(h2("Layering Activity"));
  if (agg.allInternal.length > 0) {
    items.push(para(
      `${agg.allInternal.length} internal transfers were identified between tracked wallets, totalling ` +
      `${fmtUSD(agg.allInternal.reduce((s, m) => s + m.amount_usd, 0))}. This pattern of moving funds between ` +
      `controlled addresses is a hallmark of the layering phase in money laundering schemes, designed to create ` +
      `a complex audit trail that obscures the origin of funds.`
    ));
  } else {
    items.push(para("No internal movements between tracked wallets were detected during this period."));
  }

  if (mixerTraces.length > 0) {
    items.push(h2("Mixer / Obfuscation Services"));
    items.push(alertBox(
      `${mixerTraces.length} trace(s) identified the deliberate use of Tornado Cash or equivalent mixing services. ` +
      `The use of mixing services to break the on-chain link between source and destination wallets is a deliberate ` +
      `act of obfuscation. Under FATF Recommendation 16 and relevant AML frameworks, this constitutes a red flag ` +
      `indicator of potential money laundering. The wallets involved are: ` +
      mixerTraces.map(t => t.data.target_label).join(", ") + ".",
      "HIGH"
    ));
  }

  if (exchTraces.length > 0) {
    items.push(...blank(1));
    items.push(h2("Exchange Involvement"));
    items.push(para(
      `${exchTraces.length} trace(s) terminated at identified centralised exchange hot wallets. ` +
      `Exchanges identified include: ${[...new Set(exchTraces.flatMap(t => t.data.narrative?.exchange_names || []))].filter(Boolean).join(", ") || "see trace details"}. ` +
      `This suggests funds may have been withdrawn from or deposited to centralised exchanges, ` +
      `which may be compelled to produce KYC records under appropriate legal process.`
    ));
  }

  items.push(h2("Investigative Recommendations"));
  items.push(bullet("Subpoena or legal process should be directed to identified exchanges to obtain KYC/AML records for the wallet addresses that interacted with their hot wallets."));
  items.push(bullet("Wallet addresses identified as origin points in hop traces should be subject to further blockchain analysis to determine their full transaction history."));
  items.push(bullet("The use of Tornado Cash establishes intentional obfuscation — this may be relevant to establishing mens rea in any criminal or civil proceedings."));
  items.push(bullet("Internal movements between tracked wallets should be presented as evidence of a coordinated wallet network under common control."));
  items.push(bullet("Continued monitoring is recommended. Set cron schedule to daily and review summary reports for new spike activity."));

  items.push(pageBreak());
  return items;
}

function buildAppendix(reports) {
  const last    = reports[reports.length - 1];
  const wallets = last?.data?.wallets || [];

  const items = [h1("Appendix A — Master Wallet List")];
  items.push(para(
    `The following ${wallets.length} Ethereum wallet addresses were monitored during this investigation. ` +
    `Addresses are presented with their assigned investigation labels.`
  ));
  items.push(...blank(1));

  const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
  const borders = { top: border, bottom: border, left: border, right: border };
  const colWidths = [500, 3600, 5260];

  const rows = [
    new TableRow({ children: [
      new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: "#", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
      new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: "Label", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
      new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: { fill: C.darkBlue, type: ShadingType.CLEAR }, margins: { top: 80, bottom: 80, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: "Address", size: 18, bold: true, color: C.white, font: "Arial" })] })] }),
    ]}),
    ...wallets.map((w, i) => new TableRow({ children: [
      new TableCell({ width: { size: colWidths[0], type: WidthType.DXA }, borders, shading: i % 2 === 1 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined, margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: String(i + 1), size: 18, font: "Arial" })] })] }),
      new TableCell({ width: { size: colWidths[1], type: WidthType.DXA }, borders, shading: i % 2 === 1 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined, margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: w.label, size: 18, font: "Arial" })] })] }),
      new TableCell({ width: { size: colWidths[2], type: WidthType.DXA }, borders, shading: i % 2 === 1 ? { fill: C.lightGrey, type: ShadingType.CLEAR } : undefined, margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({ children: [new TextRun({ text: w.address, size: 16, font: "Courier New", color: C.midBlue })] })] }),
    ]})),
  ];

  items.push(new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: colWidths, rows }));
  return items;
}

// ── Assemble & write ──────────────────────────────────────────────────────────

async function main() {
  console.log("Loading reports...");
  const reports = loadAllReports();
  const traces  = loadAllTraces();

  if (reports.length === 0) {
    console.error(`No eth_report_*.json files found in ${REP_DIR}`);
    process.exit(1);
  }

  console.log(`  Reports : ${reports.length}`);
  console.log(`  Traces  : ${traces.length}`);

  const agg = aggregate(reports);
  console.log(`  Wallets : ${Object.keys(agg.walletHistory).length}`);
  console.log(`  Spikes  : ${agg.allSpikes.length}`);

  console.log("Building document...");

  const children = [
    ...buildCover(reports),
    ...buildExecutiveSummary(reports, agg, traces),
    ...buildTimeline(reports),
    ...buildWalletProfiles(agg, reports),
    ...buildTraceSection(traces),
    ...buildInternalMovements(agg),
    ...buildConclusions(reports, agg, traces),
    ...buildAppendix(reports),
  ];

  const doc = new Document({
    numbering: {
      config: [
        { reference: "bullets",
          levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022", alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      ],
    },
    styles: {
      default: { document: { run: { font: "Arial", size: 22 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 36, bold: true, font: "Arial", color: C.darkBlue },
          paragraph: { spacing: { before: 360, after: 120 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 28, bold: true, font: "Arial", color: C.midBlue },
          paragraph: { spacing: { before: 280, after: 80 }, outlineLevel: 1 } },
        { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { size: 24, bold: true, font: "Arial", color: C.darkGrey },
          paragraph: { spacing: { before: 200, after: 60 }, outlineLevel: 2 } },
      ],
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              children: [
                new TextRun({ text: "CHAINSENTINEL FORENSIC ANALYSIS  —  CONFIDENTIAL", size: 16, color: C.midGrey, font: "Arial" }),
              ],
              border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.lightBlue } },
              tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              children: [
                new TextRun({ text: `Generated: ${NOW.toISOString().slice(0, 19)} UTC  |  FOR ATTORNEY USE ONLY`, size: 16, color: C.midGrey, font: "Arial" }),
              ],
              border: { top: { style: BorderStyle.SINGLE, size: 4, color: C.lightBlue } },
            }),
          ],
        }),
      },
      children,
    }],
  });

  const outPath = path.join(OUT_DIR, `forensic_report_${TS_SLUG}.docx`);
  const buffer  = await Packer.toBuffer(doc);
  fs.writeFileSync(outPath, buffer);

  console.log(`\nDone.`);
  console.log(`Report : ${outPath}`);
  console.log(`Size   : ${(buffer.length / 1024).toFixed(1)} KB`);
}

main().catch(e => { console.error(e); process.exit(1); });
