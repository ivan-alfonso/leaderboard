import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import enCommon from "./locales/en/common.json";
import enLeaderboard from "./locales/en/leaderboard.json";
import lbCommon from "./locales/lb/common.json";
import lbLeaderboard from "./locales/lb/leaderboard.json";
import frCommon from "./locales/fr/common.json";
import frLeaderboard from "./locales/fr/leaderboard.json";
import deCommon from "./locales/de/common.json";
import deLeaderboard from "./locales/de/leaderboard.json";
import itCommon from "./locales/it/common.json";
import itLeaderboard from "./locales/it/leaderboard.json";
import ptCommon from "./locales/pt/common.json";
import ptLeaderboard from "./locales/pt/leaderboard.json";

const STORAGE_KEY = "leaderboard-language";

const savedLanguage = typeof window !== "undefined"
  ? window.localStorage.getItem(STORAGE_KEY) ?? "en"
  : "en";

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { common: enCommon, leaderboard: enLeaderboard },
      lb: { common: lbCommon, leaderboard: lbLeaderboard },
      fr: { common: frCommon, leaderboard: frLeaderboard },
      de: { common: deCommon, leaderboard: deLeaderboard },
      it: { common: itCommon, leaderboard: itLeaderboard },
      pt: { common: ptCommon, leaderboard: ptLeaderboard },
    },
    lng: savedLanguage,
    fallbackLng: "en",
    defaultNS: "common",
    ns: ["common", "leaderboard"],
    interpolation: {
      escapeValue: false,
    },
  });

i18n.on("languageChanged", (lng) => {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, lng);
  }
});

export default i18n;

export const SUPPORTED_LANGUAGES = [
  { code: "en", nativeName: "English",        flag: "🇬🇧" },
  { code: "lb", nativeName: "Lëtzebuergesch", flag: "🇱🇺" },
  { code: "fr", nativeName: "Français",       flag: "🇫🇷" },
  { code: "de", nativeName: "Deutsch",        flag: "🇩🇪" },
  { code: "it", nativeName: "Italiano",       flag: "🇮🇹" },
  { code: "pt", nativeName: "Português",      flag: "🇵🇹" },
] as const;

export type LanguageCode = typeof SUPPORTED_LANGUAGES[number]["code"];
