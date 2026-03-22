import ActionBadge from "./ActionBadge";
import { formatINR } from "../../utils/format";

export default function ConcentrationTable({ data }) {
  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5">
      <h2 className="text-xs text-neutral-500 uppercase mb-4">
        Concentration
      </h2>

      <div className="grid grid-cols-6 text-[11px] text-neutral-500 pb-2">
        <div>Metric</div>
        <div className="text-right">Value</div>
        <div className="text-right">%</div>
        <div className="text-right">P&L</div>
        <div className="text-right">Limit</div>
        <div className="text-right">Action</div>
      </div>

      {data.map((r) => {
        const color = r.pnl >= 0 ? "text-green-400" : "text-red-400";

        return (
          <div
            key={r.metric}
            className="grid grid-cols-6 text-sm py-3 border-t border-neutral-800 hover:bg-neutral-800/30 transition"
          >
            <div>{r.metric}</div>
            <div className="text-right">{formatINR(r.value)}</div>
            <div className="text-right">{r.value_pct}%</div>
            <div className={`text-right ${color}`}>{formatINR(r.pnl)}</div>
            <div className="text-right text-neutral-400">{r.limit}</div>
            <div className="text-right">
              <ActionBadge action={r.action} />
            </div>
          </div>
        );
      })}
    </div>
  );
}