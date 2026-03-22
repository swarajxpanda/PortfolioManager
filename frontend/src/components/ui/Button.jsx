export default function Button({ children, onClick }) {
  return (
    <button
      onClick={onClick}
      className="bg-white text-black px-4 py-2 rounded-xl"
    >
      {children}
    </button>
  );
}