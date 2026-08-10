import { createContext, useContext, useEffect, useState } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  // True only when a stored session existed but failed verification (expired/invalid token).
  // A genuinely anonymous visitor (no token) never sets this, so ordinary customers never see
  // any auth signal — only a Founder whose session lapsed does.
  const [sessionExpired, setSessionExpired] = useState(false);
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
      .catch(() => {
        // Session expired/invalid: still clear the dead token (no privilege), but remember
        // WHY so the UI can show an unobtrusive "session expired" signal instead of silently
        // behaving as anonymous.
        localStorage.removeItem("qru_token");
        setSessionExpired(true);
      })
      .finally(() => setLoading(false));
  }, []);

  const login = async (email, password) => {
    const { data } = await api.post("/auth/login", { email, password });
    localStorage.setItem("qru_token", data.access_token);
    setUser(data.user);
    setSessionExpired(false);
    return data.user;
  };

  const logout = () => {
    localStorage.removeItem("qru_token");
    setUser(null);
    setSessionExpired(false);
  };

  return (
    <AuthContext.Provider value={{ user, loading, sessionExpired, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
