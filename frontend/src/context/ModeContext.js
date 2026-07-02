import { createContext, useContext, useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";

const ModeContext = createContext(null);

// Roles that experience QRU purely as customers.
const CONSUMER_ROLES = ["Customer", "ReadOnly"];

export function ModeProvider({ children }) {
  const { user } = useAuth();
  const [mode, setMode] = useState("enterprise");

  const isConsumerRole = user && CONSUMER_ROLES.includes(user.role);
  const canToggle = user && !isConsumerRole; // staff can preview Consumer Mode

  useEffect(() => {
    if (!user) return;
    if (isConsumerRole) {
      setMode("consumer");
      return;
    }
    const saved = localStorage.getItem("qru_mode");
    setMode(saved === "consumer" ? "consumer" : "enterprise");
  }, [user, isConsumerRole]);

  const switchMode = (next) => {
    if (isConsumerRole) return; // locked to consumer
    setMode(next);
    localStorage.setItem("qru_mode", next);
  };

  const toggleMode = () => switchMode(mode === "consumer" ? "enterprise" : "consumer");

  return (
    <ModeContext.Provider value={{ mode, isConsumer: mode === "consumer", canToggle, switchMode, toggleMode, isConsumerRole }}>
      {children}
    </ModeContext.Provider>
  );
}

export const useMode = () => useContext(ModeContext);
