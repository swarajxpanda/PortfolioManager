import { useEffect, useState } from "react";
import api from "./api/client";
import Login from "./pages/Login";
import Overview from "./pages/Overview";
import Header from "./components/layout/Header";

export default function App() {
  const [auth, setAuth] = useState(null);

  useEffect(() => {
    api.get("/auth/status")
      .then(res => setAuth(res.data.authenticated))
      .catch(() => setAuth(false));
  }, []);

  if (auth === null) return <div className="p-6">Loading...</div>;

  if (!auth) return <Login />;

  return (
    <div>
      <Header />
      <Overview />
    </div>
  );
}