import ActionBadge from "./ActionBadge";
import { formatINR } from "../../utils/format";

export default function AllocationTable({ data }) {
  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-5">
      <h2 className="text-xs text-neutral-500 uppercase mb-4">
        Asset Allocation
      </h2>

      <div className="grid grid-cols-7 text-[11px] text-neutral-500 pb-2">
        <div>Group</div>
        <div className="text-right">Value</div>
        <div className="text-right">Alloc</div>
        <div className="text-right">P&L</div>
        <div className="text-right">P&L %</div>
        <div className="text-right">Target</div>
        <div className="text-right">Action</div>
      </div>

      {data.map((r) => {
        const color = r.pnl >= 0 ? "text-green-400" : "text-red-400";

        return (
          <div
            key={r.group}
            className="grid grid-cols-7 text-sm py-3 border-t border-neutral-800 hover:bg-neutral-800/30 transition"
          >
            <div>{r.group}</div>
            <div className="text-right">{formatINR(r.value)}</div>
            <div className="text-right">{r.allocation_pct}%</div>
            <div className={`text-right ${color}`}>{formatINR(r.pnl)}</div>
            <div className={`text-right ${color}`}>{r.pnl_pct}%</div>
            <div className="text-right text-neutral-400">{r.target}</div>
            <div className="text-right">
              <ActionBadge action={r.action} />
            </div>
          </div>
        );
      })}
    </div>
  );
}