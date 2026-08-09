import { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // Only genuinely "loading" if there's a stored session to verify. An anonymous
  // visitor (no token — the common case for public/storefront traffic, including
  // crawlers and link-preview bots) has nothing to wait on, so the public routes
  // must not be held behind a network round-trip that will never resolve to a user.
  const [loading, setLoading] = useState(() => !!localStorage.getItem("qru_token"));

  useEffect(() => {
    const token = localStorage.getItem("qru_token");
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => localStorage.removeItem("qru_token"))
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("qru_token", data.access_token);
    setUser(data.user);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("qru_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
