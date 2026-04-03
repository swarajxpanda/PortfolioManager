import { Fragment, useEffect, useState } from "react";
import api from "../api/client";
import toast from "react-hot-toast";

const CLUSTER_ACCENTS = [
  "rgba(245, 158, 11, 0.55)",
  "rgba(34, 197, 94, 0.55)",
  "rgba(14, 165, 233, 0.55)",
  "rgba(244, 114, 182, 0.55)",
  "rgba(168, 85, 247, 0.55)",
  "rgba(250, 204, 21, 0.55)",
];

function formatPct(value, digits = 1) {
  return `${Number(value || 0).toFixed(digits)}%`;
}

function heatColor(value) {
  const v = Math.max(-1, Math.min(1, Number(value) || 0));
  if (v >= 0) {
    const alpha = 0.16 + v * 0.72;
    return `rgba(245, 158, 11, ${alpha})`;
  }

  const alpha = 0.16 + Math.abs(v) * 0.72;
  return `rgba(59, 130, 246, ${alpha})`;
}

function StatTile({ label, value, sublabel }) {
  return (
    <div className="rounded-2xl border border-neutral-800 bg-neutral-950/55 px-4 py-4">
      <div className="text-[11px] uppercase tracking-[0.2em] text-neutral-500">
        {label}
      </div>
      <div className="mt-2 text-2xl font-semibold text-neutral-100">
        {value}
      </div>
      {sublabel ? (
        <div className="mt-1 text-xs text-neutral-400">{sublabel}</div>
      ) : null}
    </div>
  );
}

function Heatmap({ heatmap }) {
  const symbols = heatmap?.symbols || [];
  const matrix = heatmap?.matrix || [];
  const breakSet = new Set(heatmap?.cluster_breaks || []);

  if (!symbols.length) {
    return (
      <div className="rounded-2xl border border-neutral-800 bg-neutral-950/55 p-5 text-sm text-neutral-400">
        No correlation matrix available yet.
      </div>
    );
  }

  return (
    <div className="overflow-auto">
      <div
        className="min-w-max"
        style={{
          display: "grid",
          gridTemplateColumns: `10rem repeat(${symbols.length}, 2.35rem)`,
        }}
      >
        <div className="h-10 border-b border-neutral-800" />
        {symbols.map((symbol, index) => (
          <div
            key={`col-${symbol}`}
            title={symbol}
            className={`h-10 border-b border-neutral-800 px-1 text-center text-[10px] font-medium text-neutral-500 ${
              breakSet.has(index) ? "border-l-2 border-l-neutral-700" : ""
            }`}
          >
            <div className="origin-center translate-y-4 -rotate-45 whitespace-nowrap">
              {symbol}
            </div>
          </div>
        ))}

        {symbols.map((rowSymbol, rowIndex) => (
          <Fragment key={rowSymbol}>
            <div className="sticky left-0 z-10 flex h-10 items-center border-b border-r border-neutral-800 bg-neutral-950/95 px-3 text-xs font-medium text-neutral-200">
              {rowSymbol}
            </div>
            {symbols.map((colSymbol, colIndex) => {
              const value = matrix[rowIndex]?.[colIndex] ?? 0;
              const valueLabel = Number(value || 0).toFixed(2);

              return (
                <div
                  key={`${rowSymbol}-${colSymbol}`}
                  title={`${rowSymbol} vs ${colSymbol}: ${valueLabel}`}
                  className={`h-10 border-b border-neutral-800 ${
                    breakSet.has(colIndex) ? "border-l-2 border-l-neutral-700" : ""
                  }`}
                  style={{ backgroundColor: heatColor(value) }}
                />
              );
            })}
          </Fragment>
        ))}
      </div>
    </div>
  );
}

export default function Fragility() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    setLoading(true);
    api.get("/fragility/overview")
      .then((res) => {
        setData(res.data);
        setLoading(false);
      })
      .catch(() => {
        toast.error("Failed to load portfolio fragility");
        setLoading(false);
      });
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="p-6 text-sm text-neutral-500">
        Building the correlation heatmap and cluster map...
      </div>
    );
  }

  if (!data) return null;

  const summary = data.summary || {};
  const clusters = data.clusters || [];
  const enbList = data.enb_list || [];
  const warnings = data.warnings || [];
  const strongestPair = summary.strongest_pair || {};

  return (
    <div className="mx-auto max-w-7xl space-y-5 p-6">
      <div className="rounded-[1.75rem] border border-neutral-800 bg-[radial-gradient(circle_at_top_left,_rgba(245,158,11,0.15),_transparent_35%),linear-gradient(180deg,_rgba(17,17,19,0.95),_rgba(9,9,11,0.98))] p-6 shadow-2xl shadow-black/20">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-amber-300/90">
              Portfolio Fragility
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-neutral-100">
              Correlation heatmap, clusters, and ENB
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-neutral-400">
              Ordered by the current holdings mix and the latest correlation window.
              Use this view to see which stocks move together, how those groups form
              clusters, and where the effective bets are concentrated.
            </p>
          </div>
          <button
            onClick={() => setRefreshKey((k) => k + 1)}
            className="rounded-xl border border-neutral-700 bg-neutral-900/80 px-4 py-2 text-sm font-medium text-neutral-200 transition hover:border-neutral-500 hover:bg-neutral-800 cursor-pointer"
          >
            Refresh
          </button>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <StatTile
            label="Portfolio ENB"
            value={summary.portfolio_enb?.toFixed ? summary.portfolio_enb.toFixed(2) : "0.00"}
            sublabel="Effective number of independent bets"
          />
          <StatTile
            label="Clusters"
            value={summary.cluster_count ?? 0}
            sublabel={`${summary.usable_holdings ?? 0} holdings in the matrix`}
          />
          <StatTile
            label="Largest Cluster"
            value={formatPct(summary.largest_cluster_weight)}
            sublabel="Share of total portfolio weight"
          />
          <StatTile
            label="Average Correlation"
            value={summary.avg_pairwise_corr?.toFixed ? summary.avg_pairwise_corr.toFixed(2) : "0.00"}
            sublabel="Across the selected history window"
          />
        </div>

        <div className="mt-4 rounded-2xl border border-neutral-800 bg-neutral-950/45 px-4 py-3 text-sm text-neutral-400">
          <span className="font-medium text-neutral-200">Heatmap window:</span>{" "}
          {summary.window_days || 90} days
          {strongestPair.symbols?.length === 2 ? (
            <>
              <span className="mx-3 text-neutral-700">|</span>
              <span className="font-medium text-neutral-200">Strongest pair:</span>{" "}
              {strongestPair.symbols[0]} / {strongestPair.symbols[1]} ({Number(strongestPair.corr || 0).toFixed(2)})
            </>
          ) : null}
        </div>
      </div>

      {warnings.length > 0 ? (
        <div className="rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
          {warnings.map((warning) => (
            <div key={warning}>{warning}</div>
          ))}
        </div>
      ) : null}

      <div className="rounded-2xl border border-neutral-800 bg-neutral-950/55 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-neutral-100">
              Correlation Heatmap
            </h2>
            <p className="mt-1 text-sm text-neutral-400">
              Stocks are ordered by cluster and weight so adjacent blocks are easier to scan.
            </p>
          </div>
          <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-neutral-500">
            <span className="rounded-full border border-neutral-800 bg-neutral-900 px-2 py-1">
              Low corr
            </span>
            <span className="rounded-full border border-neutral-800 bg-neutral-900 px-2 py-1">
              High corr
            </span>
          </div>
        </div>
        <div className="mt-4">
          <Heatmap heatmap={data.heatmap} />
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.25fr_0.95fr]">
        <div className="rounded-2xl border border-neutral-800 bg-neutral-950/55 p-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-neutral-100">
                Clusters and Stocks
              </h2>
              <p className="mt-1 text-sm text-neutral-400">
                Each cluster shows the holdings that move together and the cluster-level ENB.
              </p>
            </div>
          </div>

          <div className="mt-4 space-y-3">
            {clusters.map((cluster, index) => {
              const accent = CLUSTER_ACCENTS[index % CLUSTER_ACCENTS.length];

              return (
                <div
                  key={cluster.id}
                  className="rounded-2xl border bg-neutral-950/50 p-4"
                  style={{ borderColor: accent }}
                >
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                        {cluster.name}
                      </p>
                      <h3 className="mt-1 text-lg font-semibold text-neutral-100">
                        {cluster.size} stock{cluster.size === 1 ? "" : "s"}
                      </h3>
                      <p className="mt-1 text-sm text-neutral-400">
                        Average pairwise correlation {Number(cluster.avg_corr || 0).toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-semibold text-amber-300">
                        {Number(cluster.enb || 0).toFixed(2)}
                      </div>
                      <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                        ENB
                      </div>
                      <div className="mt-1 text-xs text-neutral-400">
                        {formatPct(cluster.weight_pct)} of portfolio
                      </div>
                    </div>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-2">
                    {cluster.symbols.map((item) => (
                      <span
                        key={item.symbol}
                        className="inline-flex items-center gap-2 rounded-full border border-neutral-800 bg-neutral-900/80 px-3 py-1.5 text-sm text-neutral-200"
                      >
                        <span className="font-medium">{item.symbol}</span>
                        <span className="text-xs text-neutral-500">
                          {formatPct(item.weight_pct)}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-2xl border border-neutral-800 bg-neutral-950/55 p-5">
          <div>
            <h2 className="text-base font-semibold text-neutral-100">
              ENB List
            </h2>
            <p className="mt-1 text-sm text-neutral-400">
              Stock-level ranking based on cluster-level effective bet share.
            </p>
          </div>

          <div className="mt-4 space-y-2">
            {enbList.map((item) => (
              <div
                key={`${item.symbol}-${item.cluster}`}
                className="rounded-2xl border border-neutral-800 bg-neutral-950/50 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-base font-semibold text-neutral-100">
                      {item.symbol}
                    </div>
                    <div className="text-xs text-neutral-500">{item.cluster}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-amber-300">
                      {Number(item.enb_share || 0).toFixed(2)}
                    </div>
                    <div className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">
                      ENB share
                    </div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-neutral-400">
                  <span>{formatPct(item.weight_pct)} weight</span>
                  <span>{Number(item.cluster_enb || 0).toFixed(2)} cluster ENB</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
