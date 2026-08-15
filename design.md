# Apollo Utility

Canonical design reference for future work in this repo.

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

typography:
  fontFamily:
    display: "Chakra Petch"
    mono: "IBM Plex Mono"
    body: "Inter"
  display-large:
    fontFamily: Chakra Petch
    fontSize: 40px
    fontWeight: 700
    lineHeight: 40px
    letterSpacing: "-1.5px"
    textTransform: uppercase
  display-medium:
    fontFamily: Chakra Petch
    fontSize: 28px
    fontWeight: 700
    lineHeight: 28px
    letterSpacing: "-1px"
    textTransform: uppercase
  display-small:
    fontFamily: Chakra Petch
    fontSize: 20px
    fontWeight: 700
    lineHeight: 22px
    letterSpacing: "-0.5px"
    textTransform: uppercase
  lcd-large:
    fontFamily: IBM Plex Mono
    fontSize: 32px
    fontWeight: 500
    lineHeight: 32px
    letterSpacing: "-2px"
  data-medium:
    fontFamily: IBM Plex Mono
    fontSize: 14px
    fontWeight: 500
    lineHeight: 18px
    letterSpacing: "0.25px"
  label-small:
    fontFamily: Chakra Petch
    fontSize: 12px
    fontWeight: 700
    lineHeight: 14px
    letterSpacing: "0.75px"
    textTransform: uppercase
  body-base:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: 400
    lineHeight: 22px
    letterSpacing: "0"

spacing:
  no-space: 0
  space-01: 4px
  space-02: 8px
  space-03: 12px
  space-04: 16px
  space-05: 20px
  space-06: 24px
  space-07: 32px
  space-08: 40px
  space-09: 48px
  space-10: 64px
  space-11: 80px
  space-12: 96px
  base: 4px

rounded:
  none: 0
  xs: 2px
  sm: 4px
  md: 8px
  lg: 12px
  full: 9999px

border:
  hairline: "1px solid {colors.border-secondary}"
  default: "2px solid {colors.border-primary}"
  heavy: "3px solid {colors.border-primary}"

shadow:
  hard-sm: "3px 3px 0 #121214"
  hard-md: "5px 5px 0 #121214"
  hard-lg: "8px 8px 0 #121214"
  inset-lcd: "inset 0 0 0 2px #777B63, inset 0 2px 5px rgba(18,18,20,0.22)"

components:
  button-primary:
    backgroundColor: "{colors.accent-signal}"
    textColor: "{colors.text-on-accent}"
    border: "{border.default}"
    typography: "{typography.label-small}"
    rounded: "{rounded.xs}"
    minHeight: 44px
    padding: "0 {spacing.space-04}"
    shadow: "{shadow.hard-sm}"
  button-secondary:
    backgroundColor: "{colors.background-primary}"
    textColor: "{colors.text-primary}"
    border: "{border.default}"
    typography: "{typography.label-small}"
    rounded: "{rounded.xs}"
    minHeight: 44px
    padding: "0 {spacing.space-04}"
  button-lcd:
    backgroundColor: "{colors.surface-lcd}"
    textColor: "{colors.surface-lcd-dark}"
    border: "2px solid {colors.border-lcd}"
    typography: "{typography.data-medium}"
    rounded: "{rounded.xs}"
    minHeight: 40px
    padding: "0 {spacing.space-03}"
    shadow: "{shadow.inset-lcd}"
  input:
    backgroundColor: "{colors.background-primary}"
    textColor: "{colors.text-primary}"
    border: "{border.default}"
    typography: "{typography.data-medium}"
    rounded: "{rounded.xs}"
    minHeight: 48px
    padding: "0 {spacing.space-03}"
  lcd-panel:
    backgroundColor: "{colors.surface-lcd}"
    textColor: "{colors.surface-lcd-dark}"
    border: "3px solid {colors.border-primary}"
    typography: "{typography.data-medium}"
    rounded: "{rounded.sm}"
    padding: "{spacing.space-03}"
    shadow: "{shadow.inset-lcd}"
  card:
    backgroundColor: "{colors.background-primary}"
    border: "{border.default}"
    rounded: "{rounded.sm}"
    padding: "{spacing.space-05}"
```

## Overview

A UI that feels built, not decorated.

The visual language comes from a NASA-branded Casio: industrial casing, tiny operational labels, LCD data windows, black hardware outlines, and one flash of emergency-orange nylon. It should feel precise, functional, slightly nostalgic, and almost stubbornly simple.

Think: a field instrument on a clean desk. Not a space dashboard. Not cyberpunk. Not NASA merch.

## Core Rule

Orange is a signal, not a theme.

Use `accent-signal` only for:

- The primary action
- A single selected state
- A critical notification or warning
- One meaningful progress marker

A screen should usually be 90% near-white, black, grey, and LCD olive. If orange starts appearing everywhere, the watch loses its magic and becomes a traffic cone.

## Colour Behaviour

- `background-primary` is slightly warm and faintly pink-grey, echoing the photograph's studio backdrop.
- `background-inverse` is hardware black, used for compact controls, navigation rails, or a decisive information block.
- `surface-metal` is for rare utility details: icon housings, segmented controls, equipment labels.
- `surface-lcd` is the quiet olive-beige display surface. Use it for values, status readouts, counters, timers, and technical metadata.
- Borders are visible. This system does not whisper its boundaries.

Avoid gradients, glass effects, glowing neon, soft purple shadows, or colourful status rainbows.

## Typography

Use **Chakra Petch** for the mechanical voice. Its squared forms carry the retro-technical character without becoming costume typography.

Use **IBM Plex Mono** wherever the UI is reporting a value: dates, counts, locations, status, IDs, progress, timestamps, tabs with numbers.

Use **Inter** only for readable paragraphs or explanatory copy. Keep prose short.

Rules:

- Headings are uppercase.
- Labels are uppercase, compact, and tracked out.
- Data is mono.
- Avoid oversized hero text.
- Use no more than three text sizes on a typical screen.

## Layout

Work on a strict 4px grid.

- Keep layouts flat and spacious.
- Use hard-edged panels rather than soft floating cards.
- Prefer dividers, labels, and grouping over card-on-card nesting.
- Use generous blank space around key controls.
- Align things with a machinist's ruler.

For mobile, use a 16px page gutter. For desktop, use 24px or 32px. Avoid giant rounded containers.

## Shapes, Borders, and Depth

This is softened brutalism, not a concrete bunker.

- Default corners: 2px to 4px.
- Larger panels can use 8px, but 12px is the ceiling.
- Default borders are 2px black.
- Use a 3px border only for a primary container or LCD display.
- Shadows are hard, offset, and black. No blur-heavy elevation.
- A pressed button should lose its hard shadow and shift down/right by the same amount.

## Components

### Buttons

Buttons should feel like physical controls.

- Primary: orange fill, black border, black uppercase label, hard offset shadow.
- Secondary: near-white fill, black border, no shadow unless it needs equal emphasis.
- LCD button: olive display fill, mono label, inset depth.
- Avoid pills. Buttons should be compact rectangles.

Interaction:

- Hover: orange darkens slightly or the hard shadow grows by 1px to 2px.
- Press: translate down/right, remove or reduce the hard shadow.
- Focus: 2px orange outline offset outside the black border.

### Inputs

Inputs are utility fields, not soft SaaS containers.

- 2px black border.
- Square-ish corners.
- Mono for entered values.
- A visible uppercase label above every input.
- On focus, add orange focus ring, not orange fill.

### Cards and Panels

Use cards sparingly. A card should mean: this is a distinct instrument module.

- White or LCD surface
- 2px black border
- 4px to 8px radius
- No soft shadow
- Optional hard shadow only when interactive

## Iconography

Use simple line icons with:

- 2px stroke
- Rounded line caps only when necessary
- Mostly black
- Geometric, technical, and recognisable at small sizes

Avoid filled illustration icons, gradients, emoji-style icons, or ultra-thin strokes.

## Motion

Motion should feel mechanical, not floaty.

- Button press: 80ms to 120ms
- Toggle/state change: 120ms to 160ms
- Panel reveal: 180ms to 220ms
- Use linear or a very subtle ease-out curve
- No bouncy springs, elastic overshoot, or drifting fades

Useful motifs:

- LCD digits flickering into a new value
- A small orange indicator switching on
- A segmented progress bar clicking forward
- A stamp-like confirmation appearing once, then settling

Respect reduced motion.

## Voice and Content

Short. Operational. Clear.

Good:

- `START TIMER`
- `MISSION LOG`
- `SYNC COMPLETE`
- `3 ITEMS SAVED`
- `LAST UPDATED 14:32`

Avoid:

- `You're all set!`
- `Amazing work!`
- `Let's get started`
- Long explanatory paragraphs inside the UI

The product should sound like an excellent instrument manual, not a motivational coach.

## Do

- Use orange once per view, occasionally twice when one use is a tiny status indicator.
- Make values feel tangible with LCD panels and mono type.
- Use visible borders and flat hierarchy.
- Keep screens calm, minimal, and mostly monochrome.
- Use tiny technical labels to create structure, not decoration.
- Make interactions feel pressable and physical.

## Don't

- Don't turn every component orange.
- Don't use large rounded cards, blurred shadows, glassmorphism, or gradients.
- Don't add sci-fi HUD clutter, starfields, rockets, or fake telemetry.
- Don't make every label uppercase if it harms readability.
- Don't use decorative noise or grain inside the UI.
- Don't use more than one hard-shadow treatment in a small area.

## Visual Formula

`Warm white field` + `black 2px structure` + `LCD olive data` + `one signal-orange action`

The orange strap is the whole thesis: a small, bright piece of urgency strapped onto a practical machine.
