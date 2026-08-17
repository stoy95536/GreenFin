import { createContext, useContext, useState, ReactNode, useCallback } from "react";

export type UserRole = "farmer" | "bank" | "admin";

export interface SessionUser {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  farmer_id?: string; // set after login if role is farmer
}

interface AuthContextType {
  user: SessionUser | null;
  login: (user: SessionUser) => void;
  logout: () => void;
  isLoggedIn: boolean;
  isAdmin: boolean;
  isFarmer: boolean;
  isBank: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<SessionUser | null>(null);

  const login = useCallback((u: SessionUser) => setUser(u), []);
  const logout = useCallback(() => setUser(null), []);

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        isLoggedIn: user !== null,
        isAdmin: user?.role === "admin",
        isFarmer: user?.role === "farmer",
        isBank: user?.role === "bank",
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
