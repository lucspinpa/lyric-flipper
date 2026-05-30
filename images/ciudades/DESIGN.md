---
name: Cyber-Lyric Terminal
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#b9ccb2'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#84967e'
  outline-variant: '#3b4b37'
  surface-tint: '#00e639'
  primary: '#ebffe2'
  on-primary: '#003907'
  primary-container: '#00ff41'
  on-primary-container: '#007117'
  inverse-primary: '#006e16'
  secondary: '#c6c6c7'
  on-secondary: '#2f3131'
  secondary-container: '#454747'
  on-secondary-container: '#b4b5b5'
  tertiary: '#fcf8f8'
  on-tertiary: '#313030'
  tertiary-container: '#dfdcdb'
  on-tertiary-container: '#616060'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#72ff70'
  primary-fixed-dim: '#00e639'
  on-primary-fixed: '#002203'
  on-primary-fixed-variant: '#00530e'
  secondary-fixed: '#e2e2e2'
  secondary-fixed-dim: '#c6c6c7'
  on-secondary-fixed: '#1a1c1c'
  on-secondary-fixed-variant: '#454747'
  tertiary-fixed: '#e5e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1c1b1b'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Libre Caslon Text
    fontSize: 48px
    fontWeight: '700'
    lineHeight: '1.1'
  headline-md:
    fontFamily: Libre Caslon Text
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  body-mono:
    fontFamily: Space Mono
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  label-code:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.0'
    letterSpacing: 0.1em
  display-lg-mobile:
    fontFamily: Libre Caslon Text
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
spacing:
  unit: 4px
  gutter: 24px
  margin-sm: 16px
  margin-lg: 40px
  container-max: 1200px
---

## Brand & Style

This design system is built on a "Neo-Retro Terminal" aesthetic, merging the raw, functional utility of 90s command-line interfaces with modern, high-fidelity execution. It targets a creative, tech-savvy audience that appreciates digital nostalgia, lo-fi culture, and the "hacker" ethos. 

The visual style is **Brutalist-Retro**. It utilizes a strict dark mode foundation with high-energy neon accents to create a sense of focused immersion. The personality is intentional, rhythmic, and slightly subversive, evoking the feeling of a private digital sanctuary or a clandestine data stream.

## Colors

The palette is anchored by a deep obsidian background to maximize the vibrance of the phosphorescent green accents. 

- **Primary (#00FF41):** Used exclusively for interactive states, progress indicators, and technical labels. It should feel like glowing cathode-ray tube (CRT) phosphor.
- **Secondary (#FFFFFF):** Reserved for primary content, specifically lyrical text or high-priority headlines, ensuring maximum legibility.
- **Neutral (#0A0A0A):** The void. Used for the global background and core containers.
- **Surface (#1A1A1A):** Used for subtle depth, separating secondary UI panels from the main background.

## Typography

The system utilizes a dual-font strategy to create a "Technical-Poetic" contrast.

1.  **The Poetic Layer (Serif):** Uses **Libre Caslon Text** for creative content and lyrics. This introduces a sophisticated, literary feel that breaks the rigid geometry of the UI. Use italics for emotional emphasis.
2.  **The Technical Layer (Monospace):** Uses **Space Mono** and **JetBrains Mono** for all UI elements, navigational labels, and data points. This reinforces the terminal aesthetic and ensures every character occupies a predictable width.

All UI labels should be set in uppercase with slight letter spacing to mimic legacy hardware displays.

## Layout & Spacing

The layout follows a **Fixed-Grid Terminal** model. Elements are placed with rigorous alignment to a 4px baseline grid to maintain the feel of a structured data feed.

- **Desktop:** A 12-column grid with wide 40px margins. Content is often asymmetrical, with primary narrative content on the left and technical metadata or "widgets" on the right.
- **Mobile:** A single-column flow with 16px side margins. 
- **Rhythm:** Use "Hard Gaps"—explicit white space between sections rather than soft padding—to maintain the Brutalist aesthetic.

## Elevation & Depth

This system rejects soft shadows and ambient light. Depth is achieved through **Tonal Layering** and **Hard Outlines**.

- **Level 0:** The primary background (#0A0A0A).
- **Level 1:** Containers use a #1A1A1A fill with a 1px solid border of #333333.
- **Interaction Depth:** When an element is focused or hovered, it does not lift; instead, it gains a **Primary Neon Glow** (1px solid #00FF41 border) or a pixel-style inset border.
- **Backdrop:** Use no blurs. Overlays should be 80% solid black to maintain a "low-memory" technical feel.

## Shapes

The shape language is strictly **Sharp (0px)**. There are no rounded corners in the design system. This reinforces the hardware-inspired, digital-grid nature of the interface. 

Pixel-art elements (icons, graphics) should follow a 1:1 ratio, and any "containers" for these elements should use the same hard-edged 1px border.

## Components

- **Buttons:** Rectangular with a 1px border. Default state is a white border with white text. Hover state flips to a neon green background with black text.
- **Chips / Tags:** Small, mono-spaced text surrounded by a solid 1px border. Use primary green for "active" tags.
- **Lists:** Items separated by 1px horizontal lines (#1A1A1A). Include "Line Numbers" (01, 02, 03) in primary green for a data-entry look.
- **Input Fields:** A simple underscore cursor (blinking) next to the text. Use the primary green for the cursor to simulate a terminal prompt.
- **Cards:** No shadows. Use a 1px solid border (#333333). Headers within cards should have a solid background bar to separate them from the content.
- **Pixel Graphics:** All non-textual imagery should be treated with a pixelated filter or be native pixel-art to ensure stylistic consistency with the "Space Sector" aesthetic.