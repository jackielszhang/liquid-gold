# Apollo Utility

Canonical design reference for Liquid Gold.

## Tokens

```yaml
version: alpha
name: Apollo Utility
description: A brutalist, retro-digital UI system inspired by NASA-era Casio watches. Near-white field, hard black hardware edges, LCD numerals, and one highly controlled signal-orange accent.
colors:
  background-primary: "#F5F1F4"
  background-secondary: "#E8E3E5"
  background-inverse: "#121214"
  surface-metal: "#B8B7B4"
  surface-lcd: "#D5D0B7"
  surface-lcd-dark: "#24261F"
  accent-signal: "#FF4A19"
  accent-signal-hover: "#E53C10"
  accent-signal-muted: "#FFE0D5"
  accent-signal-dark: "#A9270B"
  text-primary: "#121214"
  text-secondary: "#56545A"
  text-tertiary: "#89858B"
  text-on-inverse: "#F5F1F4"
  text-on-accent: "#121214"
  border-primary: "#121214"
  border-secondary: "#77747A"
  border-faint: "#12121426"
  border-lcd: "#777B63"
  status-positive: "#2D6A4F"
  status-warning: "#FF4A19"
  status-error: "#A9270B"
```

## Core Rule

Orange is a signal, not a theme.

Use `accent-signal` only for the primary action, a selected state, a warning, or one progress marker. A screen should usually be 90% near-white, black, grey, and LCD olive.

## Visual Formula

`Warm white field` + `black 2px structure` + `LCD olive data` + `one signal-orange action`

- Headings and labels: uppercase, compact
- Prices and dates: monospaced
- Borders are 2px black; hard offset shadows, no blur
- Motion is mechanical (80–220ms), not springy
