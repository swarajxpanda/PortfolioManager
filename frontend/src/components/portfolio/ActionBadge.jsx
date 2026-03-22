import { formatINR } from "../../utils/format";

export default function ActionBadge({ action }) {
  const base = "text-xs px-2.5 py-[3px] rounded-md border font-medium tracking-wide";
  if (action.type === "TRIM") {
  return (
    <span className={`${base} bg-neutral-800 border-neutral-700 text-neutral-200`}>
      TRIM {formatINR(action.amount)}
    </span>
  );
}

if (action.type === "ADD") {
  return (
    <span className={`${base} bg-neutral-800 border-neutral-700 text-neutral-200`}>
      ADD {formatINR(action.amount)}
    </span>
  );
}

  return (
    <span className="text-xs px-2 py-0.5 rounded bg-neutral-800 text-neutral-400 border border-neutral-700">
      HOLD
    </span>
  );
}