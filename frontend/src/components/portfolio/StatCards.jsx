import Card from "../ui/Card";
import { formatINR } from "../../utils/format";

export default function StatCards({ data }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <Card>
        <p className="text-xs text-neutral-500 uppercase">Total Value</p>
        <h2 className="text-lg font-semibold mt-1">
          {formatINR(data.total_value)}
        </h2>
      </Card>

      <Card>
        <p className="text-xs text-neutral-500 uppercase">P&L</p>
        <h2 className={`text-lg font-semibold mt-1 ${data.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
          {formatINR(data.total_pnl)}
        </h2>
      </Card>

      <Card>
        <p className="text-xs text-neutral-500 uppercase">Return</p>
        <h2 className={`text-lg font-semibold mt-1 ${data.return_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
          {data.return_pct.toFixed(1)}%
        </h2>
      </Card>

      <Card>
        <p className="text-xs text-neutral-500 uppercase">Capital at Risk</p>
        <h2 className="text-lg font-semibold mt-1 text-red-400">
          {formatINR(data.capital_at_risk)}
        </h2>
      </Card>
    </div>
  );
}