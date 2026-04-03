export default function Header() {
  return (
    <header className="border-b border-neutral-800 bg-[#0b0b0c]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.28em] text-neutral-500">
            Trading Dashboard
          </p>
          <h1 className="mt-1 text-lg font-semibold text-neutral-100">
            Portfolio intelligence workspace
          </h1>
        </div>
        <div className="text-right text-xs text-neutral-500">
          <div>Overview, exit signals, and fragility</div>
          <div className="mt-1 text-neutral-600">Built for action-first analysis</div>
        </div>
      </div>
    </header>
  );
}
