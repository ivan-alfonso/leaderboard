import React, { createContext, useContext, useEffect, useState } from "react";

export type Theme = "light" | "dark";

export interface ThemeColors {
  pageBg: string;
  surface: string;
  surfaceElevated: string;
  inputBg: string;
  hoverBg: string;
  textPrimary: string;
  textSecondary: string;
  textMuted: string;
  border: string;
  borderStrong: string;
  accent: string;
  accentHover: string;
  shadow: string;
  tableHeaderBg: string;
  tableHeaderText: string;
  tableRowAlt: string;
  tableRowSelected: string;
  tableRowHover: string;
  chartGrid: string;
  chartAxis: string;
  footerBg: string;
  footerText: string;
  footerDivider: string;
}

const lightColors: ThemeColors = {
  pageBg: "#ffffff",
  surface: "#ffffff",
  surfaceElevated: "#ffffff",
  inputBg: "#ffffff",
  hoverBg: "#f1f5f9",
  textPrimary: "#0f172a",
  textSecondary: "#334155",
  textMuted: "#64748b",
  border: "#e5e7eb",
  borderStrong: "#cbd5e1",
  accent: "#2563eb",
  accentHover: "#1d4ed8",
  shadow: "0 1px 2px rgba(15,23,42,0.04), 0 1px 3px rgba(15,23,42,0.06)",
  tableHeaderBg: "#f8fafc",
  tableHeaderText: "#0f172a",
  tableRowAlt: "#f8fafc",
  tableRowSelected: "#dbeafe",
  tableRowHover: "#f1f5f9",
  chartGrid: "#e5e7eb",
  chartAxis: "#475569",
  footerBg: "#0f172a",
  footerText: "#94a3b8",
  footerDivider: "#334155",
};

const darkColors: ThemeColors = {
  pageBg: "#0b1220",
  surface: "#111827",
  surfaceElevated: "#1e293b",
  inputBg: "#0f172a",
  hoverBg: "#334155",
  textPrimary: "#f1f5f9",
  textSecondary: "#e2e8f0",
  textMuted: "#94a3b8",
  border: "#1f2937",
  borderStrong: "#334155",
  accent: "#60a5fa",
  accentHover: "#3b82f6",
  shadow: "0 1px 3px rgba(0,0,0,0.4), 0 1px 2px rgba(0,0,0,0.3)",
  tableHeaderBg: "#0f172a",
  tableHeaderText: "#f1f5f9",
  tableRowAlt: "#0f172a",
  tableRowSelected: "#1e3a8a",
  tableRowHover: "#1f2937",
  chartGrid: "#334155",
  chartAxis: "#cbd5e1",
  footerBg: "#020617",
  footerText: "#64748b",
  footerDivider: "#1e293b",
};

interface ThemeContextValue {
  theme: Theme;
  colors: ThemeColors;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "leaderboard-theme";

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === "undefined") return "light";
    return window.localStorage.getItem(STORAGE_KEY) === "dark" ? "dark" : "light";
  });

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, theme);
      document.documentElement.setAttribute("data-theme", theme);
      document.body.style.backgroundColor = theme === "dark" ? darkColors.pageBg : lightColors.pageBg;
    }
  }, [theme]);

  const toggleTheme = () => setTheme((prev) => (prev === "light" ? "dark" : "light"));

  const colors = theme === "dark" ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ theme, colors, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextValue => {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within a ThemeProvider");
  return ctx;
};
