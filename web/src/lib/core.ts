// Shared foundations: design tokens (from the Claude Design "TYLY Dashboard" file), data access, formatting, URL state.
// The UI only selects and formats precomputed fields from app.json. The only arithmetic in this app is drawing
// geometry (bar widths, chart coordinates) and display formatting (0.128 → +12.8%, 71311 → $71.3K).
import { useEffect, useState, useSyncExternalStore } from "react";
import raw from "../data/app.json";
import { VOCAB } from "./validator.js";

export const D: any = raw;
export const WEEKS: number[] = D.meta.weeks;
export const LAST_FULL: number = D.meta.last_full_week;
export const PARTIAL: number = D.meta.partial_week;

// ---------- tokens ----------
export const C = {
  page: "#F6F3FA", ink: "#1F2636", chrome: "#232B3C", band: "#2C3548", charcoal: "#344055", sapphire: "#266DD3",
  sapphireInk: "#1F5DB5", sapphireLight: "#8EB6F5", thistle: "#DFC2F2", lav1: "#EDE6F5", lav2: "#F1ECF7", lav3: "#ECE7F2",
  muted: "#565068", body: "#3A3550", ly: "#888098", hair: "rgba(52,64,85,.13)", onDarkMuted: "#C9CFDC", onDarkFaint: "#B9C1D3",
  crit: "#C7362F", critTint: "#FBE3E1", warn: "#F2C14E", warnInk: "#3A2A00", warnText: "#7A5300", info: "#4A4060",
  winTint: "#DDF0E3", winInk: "#245E3B", up: "#2F7A4C", down: "#B8322B", upOnDark: "#8FDDB0", downOnDark: "#FF9C94",
};
export const GOALS = [
  { id: "G1", name: "Performance", hue: "#266DD3", ink: "#1F5DB5", tint: "#DCE8FA", key: "#266DD3" },
  { id: "G2", name: "Gen Z", hue: "#8A5CC9", ink: "#7346AE", tint: "#EBDDF7", key: "#8A5CC9" },
  { id: "G3", name: "Products", hue: "#344055", ink: "#344055", tint: "#E1E4EB", key: "#4A5772" },
  { id: "G4", name: "Inventory", hue: "#B0739F", ink: "#8E4F7E", tint: "#F3E1EC", key: "#B0739F" },
];
export const MONO = "'Space Mono', ui-monospace, monospace";
export const EASE = "cubic-bezier(.2,.7,.2,1)";

// ---------- formatting (display only) ----------
export const fmtMoney = (x: number | null | undefined, compact = true) =>
  x == null ? "—" : compact && Math.abs(x) >= 1000 ? `$${(x / 1000).toFixed(1)}K` : `$${x.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
export const fmtUsd0 = (x: number) => `$${Math.round(x).toLocaleString("en-US")}`;
export const fmtPct = (x: number | null | undefined, signed = false, dp = 1) => {
  if (x == null) return "—";
  const v = x * 100;
  const d = Math.abs(v) >= 100 ? 0 : dp;
  const s = Math.abs(v).toFixed(d);
  return signed ? `${v > 0 ? "+" : v < 0 ? "−" : ""}${s}%` : `${v < 0 ? "−" : ""}${s}%`;
};
export const fmtPts = (x: number | null | undefined) => (x == null ? "—" : `${x > 0 ? "+" : x < 0 ? "−" : ""}${Math.abs(x).toFixed(1)} pts`);
export const fmtNum = (x: number | null | undefined, dp = 0) =>
  x == null ? "—" : x.toLocaleString("en-US", { minimumFractionDigits: dp, maximumFractionDigits: dp });
export const fmtWos = (x: number | null | undefined) => (x == null ? "—" : x.toFixed(1));
export const arrow = (x: number | null | undefined) => (x == null || x === 0 ? "" : x > 0 ? "▲ " : "▼ ");
export const tone = (x: number | null | undefined, dark = false) =>
  x == null || x === 0 ? (dark ? C.onDarkMuted : C.muted) : x > 0 ? (dark ? C.upOnDark : C.up) : dark ? C.downOnDark : C.down;
export const dateWords = (iso: string) => {
  const d = new Date(iso + "T12:00:00Z");
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", timeZone: "UTC" }).replace(",", "");
};

// ---------- data accessors ----------
export const weekAI = (wk: number) => D.weeks_ai[String(wk)];
export const trailing = (wk: number, win: string) => D.trailing[String(wk)][win];
export const anomaly = (id: string) => D.anomalies.find((a: any) => a.id === id);
export const alertsFor = (wk: number) => (D.alerts_by_week[String(wk)] || []).map(anomaly);
export const ruleById = (id: string) => D.rules.find((r: any) => r.id === id);
export const SEV = {
  critical: { icon: "◆", label: "CRITICAL", color: C.crit, cell: C.crit },
  warning: { icon: "▲", label: "WARNING", color: C.warnText, cell: C.warn },
  info: { icon: "●", label: "INFO", color: C.info, cell: C.ly },
} as const;
export const WINDOWED = ["FAMILY_L4W_DECLINE", "WOS_LOW", "WOS_HIGH", "WOS_COLLAPSE_VS_LY", "RECEIPTS_BELOW_SALES"];
export const ruleThreshold = (id: string) => {
  const m = /([\d.]+)/.exec(ruleById(id)?.rule || "");
  return m ? parseFloat(m[1]) : null;
};

// ---------- validator checks and demos ----------
export const CHECK_INFO: { id: string; title: string; text: string }[] = VOCAB.checks;
export const checkTitle = (id: string) => CHECK_INFO.find((c) => c.id === id)?.title ?? id;
/** Briefing "&demo=<id>": variants of the week's summary built by 16_generate_summaries.py; each must fail its check. */
export const DEMOS = [
  { id: "blocked", check: "citation", label: "Edited number", hint: "One printed number is changed after rendering, so it no longer matches the fact it cites",
    banner: "one printed number in this week's AI summary was changed after rendering, so it no longer matches the fact it cites." },
  { id: "metric", check: "metric", label: "Wrong metric", hint: "A real fact is quoted under the wrong metric word",
    banner: "a sentence was put in front of this week's AI summary that quotes a real fact under the wrong metric word." },
  { id: "direction", check: "direction", label: "Wrong direction", hint: "An up or down word contradicts the sign of the change it cites",
    banner: "a sentence was put in front of this week's AI summary whose up or down word contradicts the sign of the change it cites." },
  { id: "subject", check: "subject", label: "Wrong subject", hint: "A total-business fact is put under a named customer group",
    banner: "a sentence was put in front of this week's AI summary that puts a total-business fact under a named customer group." },
];

/** Which goal a fact belongs to (colours numbers in the AI text). */
export function goalOfFact(path: string): number {
  const p = path.toLowerCase();
  if (/wos|receipts|on_hand|r1_|r2_|stock|median|excess/.test(p)) return 3;
  if (/genz|insider|returning|retention|millennial|r3_/.test(p)) return 1;
  if (/contrib|famil|tabby|share_of_growth/.test(p)) return 2;
  return 0;
}

// ---------- URL state (hash) ----------
export type Screen = "briefing" | "explore" | "ask" | "how";
export interface UrlState { screen: Screen; tab: number; wk: number; win: string; ly: boolean; demo: string }
function parse(): UrlState {
  const h = window.location.hash.replace(/^#\/?/, "");
  const [path, q = ""] = h.split("?");
  const parts = path.split("/").filter(Boolean);
  const sp = new URLSearchParams(q);
  const screen = (["briefing", "explore", "ask", "how"].includes(parts[0]) ? parts[0] : "briefing") as Screen;
  const tabM = /^g([1-4])$/.exec(parts[1] || "");
  const wk = parseInt(sp.get("wk") || "", 10);
  const win = sp.get("win") || "L4W";
  return {
    screen, tab: tabM ? parseInt(tabM[1], 10) - 1 : 0, wk: WEEKS.includes(wk) ? wk : LAST_FULL,
    win: ["L1W", "L4W", "PTD"].includes(win) ? win : "L4W", ly: sp.get("ly") !== "0", demo: sp.get("demo") || "",
  };
}
let current = parse();
const listeners = new Set<() => void>();
window.addEventListener("hashchange", () => { current = parse(); listeners.forEach((l) => l()); });
export function useUrl(): UrlState {
  return useSyncExternalStore((cb) => { listeners.add(cb); return () => listeners.delete(cb); }, () => current);
}
export function setUrl(patch: Partial<UrlState>, scrollTop = false) {
  const s = { ...current, ...patch };
  const path = s.screen === "explore" ? `explore/g${s.tab + 1}` : s.screen;
  const q = new URLSearchParams({ wk: String(s.wk), win: s.win, ...(s.ly ? {} : { ly: "0" }), ...(s.demo ? { demo: s.demo } : {}) });
  window.location.hash = `/${path}?${q}`;
  if (scrollTop) window.scrollTo({ top: 0 });
}

// Motion preference: follow the OS "reduce motion" setting unless the viewer opts in (footer toggle, saved per browser).
const motionListeners = new Set<() => void>();
const readForce = () => { try { return localStorage.getItem("tyly-motion") === "on"; } catch { return false; } };
let forceMotion = readForce();
const applyMotionClass = () => document.documentElement.classList.toggle("motion-on", forceMotion);
applyMotionClass();
export function setForceMotion(on: boolean) {
  forceMotion = on;
  try { localStorage.setItem("tyly-motion", on ? "on" : "system"); } catch { /* storage unavailable */ }
  applyMotionClass();
  motionListeners.forEach((l) => l());
}
export function useMotionPref() {
  const force = useSyncExternalStore((cb) => { motionListeners.add(cb); return () => motionListeners.delete(cb); }, () => forceMotion);
  const [sysReduce, setSys] = useState(() => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    if (!mq) return;
    const on = () => setSys(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return { force, sysReduce, reduced: sysReduce && !force };
}
export function useReducedMotion() {
  return useMotionPref().reduced;
}

/** Ask prefill handoff between screens (e.g. a card's "Ask why"). */
export const askBus = { pending: "" as string };
