import { useEffect, useState } from "react";

export default function useTheme() {
  const [theme, setTheme] = useState("dark");

  useEffect(() => {
    document.body.classList.toggle("light", theme === "light");
  }, [theme]);

  return { theme, setTheme };
}