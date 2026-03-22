export default function Card({ children }) {
  return (
    <div className="bg-neutral-900/50 border border-neutral-800 rounded-xl px-5 py-4">
      {children}
    </div>
  );
}