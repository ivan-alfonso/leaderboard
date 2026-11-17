import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useTheme } from "../contexts/ThemeContext";
import { SUPPORTED_LANGUAGES } from "../i18n/config";

// ── Customization constants ────────────────────────────────────────────────
const AGENT_TITLE      = "LëtzEval Assistant";
const FAB_SIZE         = 64;          // px — floating action button diameter
const PANEL_WIDTH      = 360;         // px
const PANEL_HEIGHT     = 480;         // px
const RETRY_DELAY_MS   = 5000;        // ms between reconnect attempts
const BAF_LOGO_SRC     = "/img/baf_logo_dark.svg";  // works on both themes
const UI_ACTION_PREFIX = "__UI_ACTION__";
// ──────────────────────────────────────────────────────────────────────────

interface ChatMessage {
  text: string;
  sender: "user" | "agent";
  isMarkdown?: boolean;
  options?: string[];   // clickable suggestion pills (from agent_reply_options)
}

// Minimal inline markdown → HTML (bold, italic, inline-code, newlines only)
function renderMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br />");
}

export const AgentComponent: React.FC = () => {
  const { colors } = useTheme();
  const { i18n } = useTranslation();

  const [isOpen, setIsOpen]           = useState(false);
  const [messages, setMessages]       = useState<ChatMessage[]>([]);
  const [input, setInput]             = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);

  // ── Agent language (independent from page i18n) ────────────────────────
  const [agentLang, setAgentLang]     = useState(i18n.language);
  const [langPickerOpen, setLangPickerOpen] = useState(false);
  const agentLangRef   = useRef(i18n.language);   // always-current value for callbacks
  const userSetLangRef = useRef(false);            // true once user explicitly picks a lang
  const langPickerRef  = useRef<HTMLDivElement>(null);
  // ──────────────────────────────────────────────────────────────────────

  const wsRef        = useRef<WebSocket | null>(null);
  const retryRef     = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef     = useRef<HTMLInputElement>(null);

  const agentUrl = import.meta.env.VITE_AGENT_URL || "ws://localhost:8765";

  // ── Helpers ──────────────────────────────────────────────────────────────

  const sendLang = (ws: WebSocket, lang: string) => {
    if (ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify({
      action: "user_set_variable",
      message: { ui_language: lang },
    }));
  };

  // ── WebSocket lifecycle ──────────────────────────────────────────────────

  const connect = () => {
    if (unmountedRef.current) return;
    if (wsRef.current && wsRef.current.readyState <= WebSocket.OPEN) return;

    setIsConnecting(true);
    try {
      const ws = new WebSocket(agentUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (unmountedRef.current) { ws.close(); return; }
        setIsConnected(true);
        setIsConnecting(false);
        // Tell agent the current agent language (may differ from page language)
        sendLang(ws, agentLangRef.current);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          const action  = payload.action as string | undefined;

          // BAF agent_reply_options: {0: "opt1", 1: "opt2", ...}
          if (action === "agent_reply_options") {
            try {
              const optMap: Record<string, string> = JSON.parse(payload.message as string);
              const opts = Object.values(optMap);
              if (opts.length > 0) {
                setMessages((prev) => [
                  ...prev,
                  { text: "", sender: "agent", options: opts },
                ]);
              }
            } catch {
              // malformed options payload — ignore
            }
            return;
          }

          let text = payload.message ?? JSON.stringify(payload);

          // Detect and dispatch UI action — never show in chat
          if (typeof text === "string" && text.startsWith(UI_ACTION_PREFIX)) {
            const jsonStr = text.slice(UI_ACTION_PREFIX.length);
            try {
              const uiAction = JSON.parse(jsonStr);
              if (uiAction.type === "apply_filters") {
                window.dispatchEvent(
                  new CustomEvent("letzeval:apply_filters", { detail: uiAction.filters })
                );
              } else if (uiAction.type === "reset_filters") {
                window.dispatchEvent(
                  new CustomEvent("letzeval:reset_filters", { detail: uiAction })
                );
              }
            } catch {
              // malformed action — ignore silently
            }
            return;
          }

          setMessages((prev) => [
            ...prev,
            { text: String(text), sender: "agent", isMarkdown: true },
          ]);
        } catch {
          setMessages((prev) => [
            ...prev,
            { text: event.data, sender: "agent" },
          ]);
        }
      };

      ws.onerror = () => {
        setIsConnecting(false);
      };

      ws.onclose = () => {
        setIsConnected(false);
        setIsConnecting(false);
        if (!unmountedRef.current) {
          retryRef.current = setTimeout(connect, RETRY_DELAY_MS);
        }
      };
    } catch {
      setIsConnecting(false);
      if (!unmountedRef.current) {
        retryRef.current = setTimeout(connect, RETRY_DELAY_MS);
      }
    }
  };

  useEffect(() => {
    unmountedRef.current = false;
    connect();
    return () => {
      unmountedRef.current = true;
      if (retryRef.current) clearTimeout(retryRef.current);
      wsRef.current?.close();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentUrl]);

  // Follow page language only when user hasn't explicitly overridden agent lang
  useEffect(() => {
    if (!userSetLangRef.current) {
      agentLangRef.current = i18n.language;
      setAgentLang(i18n.language);
      if (wsRef.current && isConnected) {
        sendLang(wsRef.current, i18n.language);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [i18n.language]);

  // Send language to agent when agentLang changes (from user picking a lang)
  useEffect(() => {
    if (isConnected && wsRef.current) {
      sendLang(wsRef.current, agentLang);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentLang, isConnected]);

  // Close lang picker on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (langPickerRef.current && !langPickerRef.current.contains(e.target as Node)) {
        setLangPickerOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      inputRef.current?.focus();
    }
  }, [messages, isOpen]);

  // ── Actions ──────────────────────────────────────────────────────────────

  const sendMessage = () => {
    if (!input.trim() || !wsRef.current || !isConnected) return;
    setMessages((prev) => [...prev, { text: input, sender: "user" }]);
    wsRef.current.send(JSON.stringify({ action: "user_message", message: input }));
    setInput("");
  };

  const resetChat = () => {
    if (!wsRef.current || !isConnected) return;
    // BAF 4.5.0 reset payload: clears session state server-side
    wsRef.current.send(JSON.stringify({ action: "reset", message: null }));
    setMessages([]);
    // Re-send language so the new session knows the selected language
    sendLang(wsRef.current, agentLangRef.current);
  };

  const sendOption = (option: string) => {
    if (!wsRef.current || !isConnected) return;
    setMessages((prev) => [...prev, { text: option, sender: "user" }]);
    wsRef.current.send(JSON.stringify({ action: "user_message", message: option }));
  };

  const selectAgentLang = (code: string) => {
    userSetLangRef.current = true;
    agentLangRef.current = code;
    setAgentLang(code);
    setLangPickerOpen(false);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const dot = isConnected ? "#22c55e" : isConnecting ? "#f59e0b" : "#ef4444";
  const currentLangEntry = SUPPORTED_LANGUAGES.find((l) => l.code === agentLang) ?? SUPPORTED_LANGUAGES[0];

  // ── Styles ───────────────────────────────────────────────────────────────

  const launcherStyle: React.CSSProperties = {
    position: "fixed",
    bottom: 60,
    right: 28,
    zIndex: 1000,
    display: "flex",
    flexDirection: "column",
    alignItems: "flex-end",
    gap: 12,
  };

  const fabStyle: React.CSSProperties = {
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: "50%",
    backgroundColor: colors.accent,
    border: "none",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 4px 16px rgba(0,0,0,0.25)",
    flexShrink: 0,
    padding: 0,
  };

  const panelStyle: React.CSSProperties = {
    width: PANEL_WIDTH,
    height: PANEL_HEIGHT,
    borderRadius: 16,
    backgroundColor: colors.surface,
    border: `1px solid ${colors.border}`,
    boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  };

  const headerStyle: React.CSSProperties = {
    padding: "12px 16px",
    borderBottom: `1px solid ${colors.border}`,
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: colors.surface,
    flexShrink: 0,
  };

  const msgAreaStyle: React.CSSProperties = {
    flex: 1,
    overflowY: "auto",
    padding: "12px 14px",
    display: "flex",
    flexDirection: "column",
    gap: 8,
  };

  const bubbleStyle = (sender: "user" | "agent"): React.CSSProperties => ({
    padding: "9px 13px",
    borderRadius: 12,
    maxWidth: "82%",
    wordWrap: "break-word",
    alignSelf: sender === "user" ? "flex-end" : "flex-start",
    backgroundColor: sender === "user" ? colors.accent : colors.pageBg,
    color: sender === "user" ? "#fff" : colors.textPrimary,
    fontSize: 13.5,
    lineHeight: 1.5,
  });

  const inputRowStyle: React.CSSProperties = {
    padding: "10px 12px",
    borderTop: `1px solid ${colors.border}`,
    display: "flex",
    gap: 8,
    flexShrink: 0,
    backgroundColor: colors.surface,
  };

  const inputStyle: React.CSSProperties = {
    flex: 1,
    padding: "8px 12px",
    border: `1px solid ${colors.border}`,
    borderRadius: 8,
    fontSize: 13.5,
    backgroundColor: colors.pageBg,
    color: colors.textPrimary,
    outline: "none",
  };

  const sendBtnStyle: React.CSSProperties = {
    padding: "8px 14px",
    backgroundColor: colors.accent,
    color: "#fff",
    border: "none",
    borderRadius: 8,
    cursor: isConnected ? "pointer" : "not-allowed",
    fontSize: 13.5,
    opacity: isConnected ? 1 : 0.55,
    flexShrink: 0,
  };

  const iconBtnStyle: React.CSSProperties = {
    background: "none",
    border: "none",
    cursor: isConnected ? "pointer" : "not-allowed",
    color: colors.textMuted,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: 4,
    borderRadius: 6,
    opacity: isConnected ? 1 : 0.45,
  };

  const langBtnStyle: React.CSSProperties = {
    background: "none",
    border: `1px solid ${colors.border}`,
    borderRadius: 6,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: 3,
    padding: "3px 6px",
    fontSize: 16,
    lineHeight: 1,
    color: colors.textMuted,
  };

  return (
    <div style={launcherStyle}>
      {isOpen && (
        <div style={panelStyle}>
          {/* Header */}
          <div style={headerStyle}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: "50%",
                  backgroundColor: dot,
                  display: "inline-block",
                  flexShrink: 0,
                }}
              />
              <span style={{ fontWeight: 600, fontSize: 14, color: colors.textPrimary }}>
                {AGENT_TITLE}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
              {/* Language selector */}
              <div ref={langPickerRef} style={{ position: "relative" }}>
                <button
                  onClick={() => setLangPickerOpen((o) => !o)}
                  style={langBtnStyle}
                  title="Agent response language"
                  aria-label="Select agent language"
                  aria-haspopup="listbox"
                  aria-expanded={langPickerOpen}
                >
                  <span aria-hidden="true">{currentLangEntry.flag}</span>
                  <svg
                    width="8" height="8" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.5"
                    strokeLinecap="round" strokeLinejoin="round"
                    aria-hidden="true"
                    style={{ transform: langPickerOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.12s ease" }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>
                {langPickerOpen && (
                  <ul
                    role="listbox"
                    aria-label="Agent language"
                    style={{
                      position: "absolute",
                      top: "calc(100% + 6px)",
                      right: 0,
                      minWidth: "180px",
                      backgroundColor: colors.surfaceElevated,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 10,
                      boxShadow: "0 8px 24px rgba(0,0,0,0.18)",
                      zIndex: 1100,
                      padding: "4px",
                      margin: 0,
                      listStyle: "none",
                    }}
                  >
                    {SUPPORTED_LANGUAGES.map((lang) => {
                      const isSelected = lang.code === agentLang;
                      return (
                        <li
                          key={lang.code}
                          role="option"
                          aria-selected={isSelected}
                          onClick={() => selectAgentLang(lang.code)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              selectAgentLang(lang.code);
                            }
                          }}
                          tabIndex={0}
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: 10,
                            padding: "7px 10px",
                            borderRadius: 6,
                            cursor: "pointer",
                            fontSize: 13,
                            fontWeight: isSelected ? 600 : 400,
                            color: isSelected ? colors.accent : colors.textPrimary,
                            backgroundColor: isSelected ? `${colors.accent}18` : "transparent",
                          }}
                          onMouseEnter={(e) => {
                            if (!isSelected) e.currentTarget.style.backgroundColor = colors.hoverBg;
                          }}
                          onMouseLeave={(e) => {
                            if (!isSelected) e.currentTarget.style.backgroundColor = "transparent";
                          }}
                        >
                          <span style={{ fontSize: 18, lineHeight: 1 }} aria-hidden="true">{lang.flag}</span>
                          <span>{lang.nativeName}</span>
                          {isSelected && (
                            <svg
                              width="12" height="12" viewBox="0 0 24 24" fill="none"
                              stroke="currentColor" strokeWidth="2.5"
                              strokeLinecap="round" strokeLinejoin="round"
                              style={{ marginLeft: "auto", color: colors.accent }}
                              aria-hidden="true"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
              {/* Reset button */}
              <button
                onClick={resetChat}
                disabled={!isConnected}
                style={iconBtnStyle}
                title="Reset conversation"
                aria-label="Reset conversation"
              >
                {/* Rotate-CCW icon */}
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 .49-4.51" />
                </svg>
              </button>
              {/* Close button */}
              <button
                onClick={() => setIsOpen(false)}
                style={{ ...iconBtnStyle, opacity: 1, cursor: "pointer" }}
                aria-label="Close chat"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          </div>

          {/* Messages */}
          <div style={msgAreaStyle}>
            {messages.length === 0 && (
              <div
                style={{
                  textAlign: "center",
                  color: colors.textMuted,
                  fontSize: 13,
                  paddingTop: 24,
                }}
              >
                {isConnected
                  ? "Ask me about the leaderboard…"
                  : isConnecting
                  ? "Connecting…"
                  : "Agent offline"}
              </div>
            )}
            {messages.map((msg, i) =>
              msg.options ? (
                <div key={i} style={{ display: "flex", flexWrap: "wrap", gap: 6, alignSelf: "flex-start" }}>
                  {msg.options.map((opt, j) => (
                    <button
                      key={j}
                      onClick={() => sendOption(opt)}
                      disabled={!isConnected}
                      style={{
                        padding: "6px 12px",
                        borderRadius: 16,
                        border: `1px solid ${colors.accent}`,
                        background: "transparent",
                        color: colors.accent,
                        cursor: isConnected ? "pointer" : "not-allowed",
                        fontSize: 13,
                        whiteSpace: "nowrap",
                      }}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              ) : msg.isMarkdown ? (
                <div
                  key={i}
                  style={bubbleStyle(msg.sender)}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                />
              ) : (
                <div key={i} style={bubbleStyle(msg.sender)}>
                  {msg.text}
                </div>
              )
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input row */}
          <div style={inputRowStyle}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKey}
              placeholder={isConnected ? "Type a message…" : "Not connected"}
              disabled={!isConnected}
              style={inputStyle}
            />
            <button onClick={sendMessage} disabled={!isConnected} style={sendBtnStyle}>
              Send
            </button>
          </div>
        </div>
      )}

      {/* FAB — BAF logo when closed, chevron-down when open */}
      <button
        style={fabStyle}
        onClick={() => setIsOpen((o) => !o)}
        aria-label={isOpen ? "Close assistant" : "Open assistant"}
        title={AGENT_TITLE}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        ) : (
          <img
            src={BAF_LOGO_SRC}
            alt="BAF"
            width={36}
            height={36}
            style={{ display: "block" }}
          />
        )}
      </button>
    </div>
  );
};
