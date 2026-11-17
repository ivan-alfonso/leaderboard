# Agent UI Customization Guide

Quick-reference for adapting the LëtzEval BAF chat widget without touching business logic.

## Named constants (`AgentComponent.tsx`)

All visual knobs are grouped at the top of the file as named constants:

| Constant | Default | Purpose |
|---|---|---|
| `AGENT_TITLE` | `"LëtzEval Assistant"` | Displayed in the chat header |
| `FAB_SIZE` | `64` | Floating action button diameter (px) |
| `PANEL_WIDTH` | `360` | Chat panel width (px) |
| `PANEL_HEIGHT` | `480` | Chat panel height (px) |
| `RETRY_DELAY_MS` | `5000` | Milliseconds between reconnect attempts |
| `BAF_LOGO_SRC` | `"/img/baf_logo_dark.svg"` | FAB icon (shown when chat is closed) |

Change a constant and the widget updates everywhere it is used — no logic hunting needed.

## BAF logo

The logo at `frontend/public/img/baf_logo_dark.svg` uses teal/cyan tones (`#23b9d6`, `#0096bb`, `#397a94`) that read well on both light and dark backgrounds, so a single file covers both themes.

To replace it with a project-specific icon:
1. Place the new SVG (or PNG) in `frontend/public/img/`.
2. Update `BAF_LOGO_SRC` in `AgentComponent.tsx`.
3. Adjust `width` / `height` on the `<img>` tag inside the FAB if the new icon needs different sizing.

## Colors

The widget uses the site-wide design token object (`colors`) from `ThemeContext`. All surface, border, accent, and text colors automatically track the user's light/dark theme.

To override a specific color — for example the user-bubble background — edit the inline `bubbleStyle` function:

```tsx
backgroundColor: sender === "user" ? "#your-color" : colors.pageBg,
```

## WebSocket URL

Set `VITE_AGENT_URL` in the frontend `.env` file (or Docker environment). The value must be a `ws://` or `wss://` URL pointing at the running BAF agent.

```
VITE_AGENT_URL=wss://your-domain.example.com/ws
```

**Production must use `wss://`** (TLS). Never hardcode a `ws://localhost` URL in a production build.

## Language synchronization

The widget automatically detects the site's current language via `i18n.language` and sends it to the agent over WebSocket on:

- Initial connection (`ws.onopen`)
- Every subsequent language change (`i18n.language` change)
- After a chat reset

The agent stores it in `session.get('ui_language')` and uses it for all reply text. No manual configuration needed.

## Reset button

The reset button in the chat header sends `{"action":"reset","message":null}` to the BAF agent, which clears the server-side session state. The client-side message history is also cleared, and the current UI language is re-sent so the new session starts in the correct language.

## Adding new UI actions

The agent can push `__UI_ACTION__{"type":"..."}` messages to the frontend. New action types are handled in the `ws.onmessage` block in `AgentComponent.tsx`:

```tsx
} else if (action.type === "your_new_type") {
  window.dispatchEvent(new CustomEvent("letzeval:your_event", { detail: action }));
}
```

The corresponding `CustomEvent` listener goes in whichever React component needs to react to it (currently `ModelMetricsBarChart.tsx` for filter/reset actions).
