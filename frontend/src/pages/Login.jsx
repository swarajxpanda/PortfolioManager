export default function Login() {
  return (
    <div className="h-screen flex items-center justify-center bg-black text-white">
      <button
        onClick={() =>
          (window.location.href = "http://localhost:8000/api/auth/login")
        }
        className="bg-white text-black px-6 py-3 rounded-xl"
      >
        Login with Kite
      </button>
    </div>
  );
}