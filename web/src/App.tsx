import Ask from "./components/Ask";
import Briefing from "./components/Briefing";
import Explore from "./components/Explore";
import Header from "./components/Header";
import HowBuilt from "./components/HowBuilt";
import { LikeForLikeStrip } from "./components/LikeForLike";
import { C, MONO, setForceMotion, useMotionPref, useUrl } from "./lib/core";

function MotionToggle() {
  const m = useMotionPref();
  return (
    <span style={{ whiteSpace: "nowrap" }}>
      Animations: <span className="link" onClick={() => setForceMotion(!m.force)}>{m.force ? "always on" : m.sysReduce ? "off (system reduce-motion)" : "on"}</span>
      {m.sysReduce && !m.force && " · click to play them anyway"}
    </span>
  );
}

export default function App() {
  const u = useUrl();
  return (
    <div style={{ minHeight: "100vh", background: C.page, color: C.ink }}>
      <Header />
      <LikeForLikeStrip />
      {u.demo === "blocked" && u.screen === "briefing" && (
        <div className="pad-x" style={{ padding: "9px 40px", background: C.critTint, color: C.crit, fontSize: 12.5, fontFamily: MONO }}>
          Validator demo: the first percentage in this week's AI summary was raised by one point on purpose, to show what happens when a number doesn't match its source.
        </div>
      )}
      {u.screen === "briefing" && <Briefing />}
      {u.screen === "explore" && <Explore key={u.tab} />}
      {u.screen === "ask" && <Ask />}
      {u.screen === "how" && <HowBuilt />}
      <footer className="pad-x" style={{ display: "flex", gap: 16, flexWrap: "wrap", justifyContent: "space-between", padding: "22px 40px 40px", fontSize: 12, color: C.muted, fontFamily: MONO, borderTop: `1px solid ${C.hair}` }}>
        <span>Sample extract · FY26 vs FY25 · every number from metrics.json / anomalies.json · AI text worded by Claude and checked by a validator</span>
        <MotionToggle />
      </footer>
    </div>
  );
}
