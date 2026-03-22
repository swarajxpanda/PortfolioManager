import { useEffect, useState } from "react";
import api from "../../api/client";
import toast from "react-hot-toast";

export default function SettingsPanel({ onClose, onSaved }) {
  const [config, setConfig] = useState(null);
  const [holdings, setHoldings] = useState([]);
  const [saving, setSaving] = useState(false);
  const [newGroup, setNewGroup] = useState("");
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api.get("/portfolio/settings")
      .then(res => {
        setConfig(structuredClone(res.data.config));
        setHoldings(res.data.holdings || []);
      })
      .catch(() => toast.error("Failed to load settings"));
  }, []);

  if (!config) return null;

  /* ───── computed ───── */

  // build symbol → group lookup
  const symbolGroup = {};
  for (const [group, syms] of Object.entries(config.groups)) {
    for (const sym of syms) {
      symbolGroup[sym] = group;
    }
  }

  const groupNames = Object.keys(config.groups);
  const unassignedCount = holdings.filter(s => !symbolGroup[s]).length;

  // filtered & sorted holdings
  const filteredHoldings = holdings
    .filter(s => s.toLowerCase().includes(filter.toLowerCase()))
    .sort((a, b) => {
      const ga = symbolGroup[a] || "";
      const gb = symbolGroup[b] || "";
      if (!ga && gb) return -1;  // unassigned first
      if (ga && !gb) return 1;
      if (ga !== gb) return ga.localeCompare(gb);
      return a.localeCompare(b);
    });

  /* ───── handlers ───── */

  const assignStock = (symbol, newGroupName) => {
    const s = structuredClone(config);
    // remove from old group
    for (const g of Object.keys(s.groups)) {
      s.groups[g] = s.groups[g].filter(x => x !== symbol);
    }
    // add to new group (if not "unassigned")
    if (newGroupName && s.groups[newGroupName]) {
      s.groups[newGroupName].push(symbol);
    }
    setConfig(s);
  };

  const assignAllUnassigned = (groupName) => {
    const s = structuredClone(config);
    for (const sym of holdings) {
      const alreadyAssigned = Object.values(s.groups).some(arr => arr.includes(sym));
      if (!alreadyAssigned && s.groups[groupName]) {
        s.groups[groupName].push(sym);
      }
    }
    setConfig(s);
  };

  const addGroup = () => {
    const name = newGroup.trim();
    if (!name || config.groups[name]) return;
    const s = structuredClone(config);
    s.groups[name] = [];
    s.targets[name] = [0, 0];
    setConfig(s);
    setNewGroup("");
  };

  const removeGroup = (name) => {
    const s = structuredClone(config);
    delete s.groups[name];
    delete s.targets[name];
    setConfig(s);
  };

  const renameGroup = (oldName, newName) => {
    if (!newName || newName === oldName) return;
    const s = structuredClone(config);
    s.groups[newName] = s.groups[oldName] || [];
    delete s.groups[oldName];
    if (s.targets[oldName]) {
      s.targets[newName] = s.targets[oldName];
      delete s.targets[oldName];
    }
    setConfig(s);
  };

  const setTarget = (group, idx, val) => {
    const s = structuredClone(config);
    if (!s.targets[group]) s.targets[group] = [0, 0];
    s.targets[group][idx] = Number(val) || 0;
    setConfig(s);
  };

  const setConc = (key, val) => {
    const s = structuredClone(config);
    s.concentration[key] = Number(val) || 0;
    setConfig(s);
  };

  /* ───── save / reset ───── */

  const handleSave = async () => {
    if (unassignedCount > 0) {
      toast.error(`${unassignedCount} stock(s) still unassigned`);
      return;
    }
    setSaving(true);
    try {
      await api.put("/portfolio/settings", config);
      toast.success("Settings saved");
      onSaved?.();
    } catch {
      toast.error("Save failed");
    }
    setSaving(false);
  };

  const handleReset = async () => {
    try {
      const res = await api.post("/portfolio/settings/reset");
      setConfig(structuredClone(res.data.config));
      toast.success("Reset to defaults");
      onSaved?.();
    } catch {
      toast.error("Reset failed");
    }
  };

  /* ───── styles ───── */

  const input =
    "bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-1.5 text-sm text-neutral-200 " +
    "focus:outline-none focus:border-neutral-500 transition w-full";

  const smallBtn = (color = "neutral") => {
    const map = {
      neutral: "bg-neutral-800 hover:bg-neutral-700 border-neutral-700 text-neutral-300",
      red:     "bg-red-500/10 hover:bg-red-500/20 border-red-500/30 text-red-400",
      green:   "bg-emerald-500/10 hover:bg-emerald-500/20 border-emerald-500/30 text-emerald-400",
    };
    return `text-xs px-2.5 py-1 rounded-lg border font-medium transition cursor-pointer ${map[color]}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* panel */}
      <div className="relative w-full max-w-xl bg-[#111113] border-l border-neutral-800 overflow-y-auto">
        {/* header */}
        <div className="sticky top-0 z-10 bg-[#111113]/90 backdrop-blur border-b border-neutral-800 px-6 py-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-neutral-200 tracking-wide uppercase">
            Overview Settings
          </h2>
          <button onClick={onClose} className="text-neutral-500 hover:text-neutral-300 transition cursor-pointer">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="px-6 py-5 space-y-6">

          {/* ─── STOCK ASSIGNMENT TABLE ─── */}
          <section className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs text-neutral-500 uppercase tracking-wide">Assign Stocks to Groups</h3>
              {unassignedCount > 0 && (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30 font-medium">
                  {unassignedCount} unassigned
                </span>
              )}
            </div>

            {/* quick-assign all unassigned */}
            {unassignedCount > 0 && (
              <div className="flex items-center gap-2 text-xs text-neutral-400">
                <span>Assign all unassigned to:</span>
                <select
                  onChange={e => { if (e.target.value) assignAllUnassigned(e.target.value); e.target.value = ""; }}
                  className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1 text-xs text-neutral-200 cursor-pointer"
                  defaultValue=""
                >
                  <option value="" disabled>Select group…</option>
                  {groupNames.map(g => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
            )}

            {/* search */}
            <input
              value={filter}
              onChange={e => setFilter(e.target.value)}
              placeholder="Search stocks…"
              className={`${input} !py-1.5`}
            />

            {/* table header */}
            <div className="grid grid-cols-2 text-[11px] text-neutral-500 pb-1 border-b border-neutral-800">
              <div>Stock</div>
              <div>Group</div>
            </div>

            {/* stock rows */}
            <div className="max-h-[300px] overflow-y-auto space-y-0.5 pr-1">
              {filteredHoldings.map(sym => {
                const group = symbolGroup[sym] || "";
                const isUnassigned = !group;

                return (
                  <div
                    key={sym}
                    className={`grid grid-cols-2 items-center py-1.5 px-1 rounded-lg transition ${
                      isUnassigned ? "bg-amber-500/5" : "hover:bg-neutral-800/40"
                    }`}
                  >
                    <span className={`text-sm ${isUnassigned ? "text-amber-300" : "text-neutral-300"}`}>
                      {sym}
                    </span>
                    <select
                      value={group}
                      onChange={e => assignStock(sym, e.target.value)}
                      className={`bg-neutral-800 border rounded-lg px-2 py-1 text-xs cursor-pointer transition ${
                        isUnassigned
                          ? "border-amber-500/40 text-amber-300"
                          : "border-neutral-700 text-neutral-200"
                      }`}
                    >
                      <option value="">— Unassigned —</option>
                      {groupNames.map(g => <option key={g} value={g}>{g}</option>)}
                    </select>
                  </div>
                );
              })}
            </div>
          </section>

          {/* ─── MANAGE GROUPS ─── */}
          <section className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5 space-y-3">
            <h3 className="text-xs text-neutral-500 uppercase tracking-wide">Manage Groups</h3>

            {groupNames.map(group => (
              <div key={group} className="flex items-center gap-2">
                <input
                  value={group}
                  onChange={e => renameGroup(group, e.target.value)}
                  className={`${input} font-medium !py-1 flex-1`}
                />
                <span className="text-[11px] text-neutral-500 w-6 text-center">
                  {config.groups[group].length}
                </span>
                <button onClick={() => removeGroup(group)} className={smallBtn("red")}>
                  ×
                </button>
              </div>
            ))}

            <div className="flex gap-2 pt-2 border-t border-neutral-800">
              <input
                value={newGroup}
                onChange={e => setNewGroup(e.target.value)}
                onKeyDown={e => e.key === "Enter" && addGroup()}
                placeholder="New group name…"
                className={input}
              />
              <button onClick={addGroup} className={smallBtn("green")}>
                + Add
              </button>
            </div>
          </section>

          {/* ─── ALLOCATION TARGETS ─── */}
          <section className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5 space-y-3">
            <h3 className="text-xs text-neutral-500 uppercase tracking-wide">Allocation Targets</h3>

            <div className="grid grid-cols-3 text-[11px] text-neutral-500 pb-1">
              <div>Group</div>
              <div className="text-center">Min %</div>
              <div className="text-center">Max %</div>
            </div>

            {Object.entries(config.targets).map(([group, [min, max]]) => (
              <div key={group} className="grid grid-cols-3 items-center gap-3">
                <span className="text-sm text-neutral-300">{group}</span>
                <input
                  type="number"
                  value={min}
                  onChange={e => setTarget(group, 0, e.target.value)}
                  className={`${input} text-center`}
                />
                <input
                  type="number"
                  value={max}
                  onChange={e => setTarget(group, 1, e.target.value)}
                  className={`${input} text-center`}
                />
              </div>
            ))}
          </section>

          {/* ─── CONCENTRATION LIMITS ─── */}
          <section className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5 space-y-3">
            <h3 className="text-xs text-neutral-500 uppercase tracking-wide">Concentration Limits</h3>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <label className="text-sm text-neutral-300">Top 5 Holdings Limit</label>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    value={config.concentration.top5}
                    onChange={e => setConc("top5", e.target.value)}
                    className={`${input} !w-20 text-center`}
                  />
                  <span className="text-xs text-neutral-500">%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="text-sm text-neutral-300">Single Stock Limit</label>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number"
                    value={config.concentration.single}
                    onChange={e => setConc("single", e.target.value)}
                    className={`${input} !w-20 text-center`}
                  />
                  <span className="text-xs text-neutral-500">%</span>
                </div>
              </div>
            </div>
          </section>

        </div>

        {/* ─── footer ─── */}
        <div className="sticky bottom-0 bg-[#111113]/90 backdrop-blur border-t border-neutral-800 px-6 py-4 flex items-center justify-between">
          <button
            onClick={handleReset}
            className="text-xs text-neutral-400 hover:text-neutral-200 transition cursor-pointer underline underline-offset-2"
          >
            Reset to Defaults
          </button>

          <div className="flex items-center gap-3">
            {unassignedCount > 0 && (
              <span className="text-[11px] text-amber-400">
                {unassignedCount} unassigned
              </span>
            )}
            <button
              onClick={handleSave}
              disabled={saving || unassignedCount > 0}
              className="bg-white text-black text-sm font-medium px-5 py-2 rounded-xl hover:bg-neutral-200 transition disabled:opacity-40 cursor-pointer"
            >
              {saving ? "Saving…" : "Save Settings"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
