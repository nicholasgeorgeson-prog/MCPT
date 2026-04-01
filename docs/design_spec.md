# MCPT — Design System Specification ("Slate")

## Design Philosophy

MCPT uses the **"Slate"** design language. The guiding principle is **"Apple for enterprise"** —
a surface so clean and purposeful that users never have to think about the interface, only the work.

**Three rules that govern every design decision:**
1. **Every element earns its place.** If it doesn't help the user understand the promotion cycle or take an action, it doesn't exist.
2. **State is always visible.** A user should know the status of any diagram at a glance. Never force them to click to discover state.
3. **Complex back end, invisible complexity.** The 49-field API, the three-identifier GUID/DSLID model, the SQL joins — none of that surfaces in the UI. The UI is effortless.

**What Slate is NOT:**
- It is not AEGIS. AEGIS is warm cream and gold — an aerospace documentary. MCPT is a precision instrument.
- It is not cluttered. No gradients on data, no decorative borders, no competing visual elements.
- It is not flat either. Elevation, shadow, and depth are used deliberately to communicate hierarchy.

---

## Color System

### CSS Custom Properties — Light Mode (Default)

```css
:root {
  /* === Backgrounds — Cool White Scale === */
  --bg-base:        #FFFFFF;          /* Pure white — main app background */
  --bg-surface:     #F8FAFC;          /* Card surfaces, panels, sidebar */
  --bg-elevated:    #F1F5F9;          /* Hovered cards, secondary surfaces */
  --bg-overlay:     #E2E8F0;          /* Active/pressed, dividers */
  --bg-input:       #FFFFFF;          /* Text inputs — always white (Apple style) */
  --bg-input-focus: #FAFBFF;          /* Very subtle blue tint on focus */
  --bg-backdrop:    rgba(15,23,42,0.4); /* Modal backdrop — cool dark */

  /* === Text — Cool-Toned Slate === */
  --text-primary:   #0F172A;          /* Near-black, cool-toned (Slate 900) */
  --text-secondary: #475569;          /* Secondary content (Slate 600) */
  --text-muted:     #94A3B8;          /* Disabled, placeholders (Slate 400) */
  --text-disabled:  #CBD5E1;          /* Fully inactive (Slate 300) */
  --text-inverse:   #FFFFFF;          /* On dark/accent backgrounds */
  --text-link:      #2563EB;          /* Links */

  /* === MCPT Brand / Primary Accent — Confident Blue === */
  --mcpt-navy:      #1E3A5F;          /* Deep navy — header brand color */
  --mcpt-navy-dark: #142847;          /* Darker navy for hover on brand elements */
  --accent:         #2563EB;          /* Primary interactive blue (Slate-derived Blue 600) */
  --accent-hover:   #1D4ED8;          /* Hover (Blue 700) */
  --accent-emphasis:#1E40AF;          /* Strong emphasis (Blue 800) */
  --accent-light:   #EFF6FF;          /* Background tint (Blue 50) */
  --accent-muted:   rgba(37,99,235,0.15); /* Muted tint for highlights */
  --accent-glow:    rgba(37,99,235,0.25); /* Focus glow, active ring */
  --accent-fg:      #FFFFFF;          /* Text on accent background */

  /* === Promotion Cycle Status Colors — THE CORE UI LANGUAGE === */
  /* These four states are the most important colors in the entire app */
  --status-draft:        #6366F1;          /* Indigo — diagram in Draft state */
  --status-draft-bg:     rgba(99,102,241,0.08);
  --status-draft-border: rgba(99,102,241,0.25);

  --status-authorized:   #F59E0B;          /* Amber — authorized, awaiting promotion */
  --status-auth-bg:      rgba(245,158,11,0.08);
  --status-auth-border:  rgba(245,158,11,0.25);

  --status-master:       #10B981;          /* Emerald — promoted to Master */
  --status-master-bg:    rgba(16,185,129,0.08);
  --status-master-border:rgba(16,185,129,0.25);

  --status-archived:     #94A3B8;          /* Slate — archived/inactive */
  --status-archived-bg:  rgba(148,163,184,0.08);
  --status-archived-border:rgba(148,163,184,0.25);

  /* === Three-State Boolean Colors === */
  --bool-true:       #10B981;          /* ✓ Green (Emerald 500) */
  --bool-true-bg:    rgba(16,185,129,0.08);
  --bool-false:      #EF4444;          /* ✗ Red (Red 500) */
  --bool-false-bg:   rgba(239,68,68,0.08);
  --bool-null:       #94A3B8;          /* — Slate (unknown/N/A) */
  --bool-null-bg:    rgba(148,163,184,0.08);

  /* === Semantic Status (global) === */
  --success:         #059669;  --success-hover: #047857;
  --success-bg:      rgba(5,150,105,0.08);
  --success-border:  rgba(5,150,105,0.25);

  --warning:         #D97706;  --warning-hover: #B45309;
  --warning-bg:      rgba(217,119,6,0.08);
  --warning-border:  rgba(217,119,6,0.25);

  --error:           #DC2626;  --error-hover: #B91C1C;
  --error-bg:        rgba(220,38,38,0.08);
  --error-border:    rgba(220,38,38,0.25);

  --info:            #0284C7;  --info-hover: #0369A1;
  --info-bg:         rgba(2,132,199,0.08);
  --info-border:     rgba(2,132,199,0.25);

  /* === Borders === */
  --border-default:  #E2E8F0;          /* Standard border (Slate 200) */
  --border-muted:    #F1F5F9;          /* Very subtle (Slate 100) */
  --border-emphasis: #CBD5E1;          /* Strong border (Slate 300) */
  --border-focus:    var(--accent);    /* Focus ring color */

  /* === Sidebar === */
  --sidebar-bg:      #F8FAFC;
  --sidebar-active:  var(--accent-light);
  --sidebar-active-border: var(--accent);
  --sidebar-hover:   #F1F5F9;

  /* === Table === */
  --table-header-bg: #F8FAFC;
  --table-row-hover: rgba(37,99,235,0.04);
  --table-row-selected: rgba(37,99,235,0.08);
  --table-border:    #E2E8F0;

  /* === Scrollbar === */
  --scrollbar-thumb: #CBD5E1;
  --scrollbar-track: transparent;
}
```

### CSS Custom Properties — Dark Mode

```css
[data-theme="dark"], .dark-mode {
  --bg-base:        #0F172A;          /* Slate 900 */
  --bg-surface:     #1E293B;          /* Slate 800 */
  --bg-elevated:    #293548;          /* Intermediate */
  --bg-overlay:     #334155;          /* Slate 700 */
  --bg-input:       #1E293B;          /* Dark inputs */
  --bg-input-focus: #243350;
  --bg-backdrop:    rgba(0,0,0,0.65);

  --text-primary:   #F1F5F9;          /* Slate 100 */
  --text-secondary: #94A3B8;          /* Slate 400 */
  --text-muted:     #64748B;          /* Slate 500 */
  --text-disabled:  #475569;          /* Slate 600 */
  --text-link:      #60A5FA;

  --mcpt-navy:      #1E3A5F;
  --accent:         #3B82F6;          /* Brighter blue in dark (Blue 500) */
  --accent-hover:   #2563EB;
  --accent-light:   rgba(59,130,246,0.12);
  --accent-muted:   rgba(59,130,246,0.2);
  --accent-glow:    rgba(59,130,246,0.3);

  --status-draft:        #818CF8;     /* Softer indigo in dark */
  --status-draft-bg:     rgba(129,140,248,0.12);
  --status-authorized:   #FCD34D;     /* Brighter amber */
  --status-auth-bg:      rgba(252,211,77,0.12);
  --status-master:       #34D399;     /* Brighter emerald */
  --status-master-bg:    rgba(52,211,153,0.12);

  --bool-true:      #34D399;
  --bool-false:     #F87171;
  --bool-null:      #64748B;

  --border-default:  #334155;         /* Slate 700 */
  --border-muted:    #1E293B;
  --border-emphasis: #475569;

  --sidebar-bg:      #1E293B;
  --sidebar-active:  rgba(59,130,246,0.15);
  --sidebar-hover:   rgba(255,255,255,0.05);
  --table-header-bg: #1E293B;
  --table-row-hover: rgba(59,130,246,0.06);
  --scrollbar-thumb: #334155;
}
```

---

## Typography

```css
:root {
  /* Font stacks — Inter as primary (closest to SF Pro for web) */
  --font-sans: 'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Noto Sans', sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas, 'Liberation Mono', monospace;

  /* Scale — 15px base (slightly more generous than AEGIS for "Apple spacious" feel) */
  --font-2xs:   10px;    /* Smallest badges, metadata */
  --font-xs:    11px;    /* Secondary labels, timestamps */
  --font-sm:    13px;    /* Body text, form labels */
  --font-base:  15px;    /* Default reading size */
  --font-md:    16px;    /* Prominent body, card descriptions */
  --font-lg:    18px;    /* Card titles, section headers */
  --font-xl:    20px;    /* Page titles */
  --font-2xl:   24px;    /* Major section headers */
  --font-3xl:   30px;    /* Modal headers, hero numbers */
  --font-4xl:   36px;    /* Landing stats */

  /* Weights */
  --weight-normal:   400;
  --weight-medium:   500;
  --weight-semibold: 600;
  --weight-bold:     700;

  /* Line heights */
  --leading-tight:   1.2;
  --leading-snug:    1.35;
  --leading-normal:  1.5;
  --leading-relaxed: 1.65;

  /* Letter spacing */
  --tracking-tight:  -0.02em;
  --tracking-normal:  0;
  --tracking-wide:    0.02em;
  --tracking-wider:   0.06em;   /* Uppercase labels */
  --tracking-widest:  0.1em;
}
```

---

## Spacing (4px Grid)

```css
:root {
  --sp-0:  0;      --sp-1:  4px;   --sp-2:  8px;   --sp-3:  12px;
  --sp-4:  16px;   --sp-5:  20px;  --sp-6:  24px;  --sp-7:  28px;
  --sp-8:  32px;   --sp-10: 40px;  --sp-12: 48px;  --sp-16: 64px;
  --sp-20: 80px;   --sp-24: 96px;
}
```

---

## Border Radius

```css
:root {
  --r-none:  0;       --r-xs:  3px;    --r-sm:  5px;
  --r-md:    8px;     /* Buttons, inputs — Apple-standard rounding */
  --r-lg:    12px;    /* Cards, panels */
  --r-xl:    16px;    /* Modals, large cards */
  --r-2xl:   24px;    /* Feature cards, hero elements */
  --r-full:  9999px;  /* Pills, avatars, badges */
}
```

---

## Shadow / Elevation System

```css
:root {
  /* Cool-tinted shadows (blue-grey rather than warm) */
  --shadow-xs:  0 1px 2px rgba(15,23,42,0.04);
  --shadow-sm:  0 1px 3px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
  --shadow-md:  0 4px 8px -2px rgba(15,23,42,0.08), 0 2px 4px -2px rgba(15,23,42,0.04);
  --shadow-lg:  0 12px 24px -4px rgba(15,23,42,0.10), 0 4px 8px -2px rgba(15,23,42,0.05);
  --shadow-xl:  0 24px 48px -8px rgba(15,23,42,0.12), 0 8px 16px -4px rgba(15,23,42,0.06);
  --shadow-2xl: 0 40px 80px -12px rgba(15,23,42,0.20);
  --shadow-inner: inset 0 2px 4px rgba(15,23,42,0.06);
  --shadow-focus: 0 0 0 3px var(--accent-glow);
  --shadow-focus-error: 0 0 0 3px rgba(220,38,38,0.2);
  --shadow-blue-glow: 0 0 20px rgba(37,99,235,0.15), 0 4px 12px rgba(15,23,42,0.08);
}
```

---

## Animation System

```css
:root {
  /* Durations — "Snappy but not rushed" (Apple's signature feel) */
  --dur-instant:  50ms;
  --dur-fast:     120ms;    /* Hover states, button press */
  --dur-normal:   200ms;    /* Tab switches, dropdown open */
  --dur-medium:   300ms;    /* Modals, panel slides */
  --dur-slow:     400ms;    /* Page transitions, demo animations */
  --dur-slower:   500ms;    /* Complex animations, welcome sequences */

  /* Easings — Apple-inspired spring and ease-out are dominant */
  --ease-linear:   linear;
  --ease-in:       cubic-bezier(0.4, 0, 1, 1);
  --ease-out:      cubic-bezier(0, 0, 0.2, 1);      /* Most common — decelerating */
  --ease-in-out:   cubic-bezier(0.4, 0, 0.2, 1);    /* Symmetric */
  --ease-spring:   cubic-bezier(0.175, 0.885, 0.32, 1.275); /* Playful spring */
  --ease-default:  var(--ease-out);
}

/* Standard interactive transition — applies to ALL interactive elements */
.interactive {
  transition:
    color          var(--dur-fast)   var(--ease-default),
    background     var(--dur-fast)   var(--ease-default),
    border-color   var(--dur-fast)   var(--ease-default),
    box-shadow     var(--dur-fast)   var(--ease-default),
    transform      var(--dur-fast)   var(--ease-default),
    opacity        var(--dur-fast)   var(--ease-default);
}
```

---

## Z-Index Scale

```css
:root {
  --z-base:         0;
  --z-raised:       10;
  --z-dropdown:     100;
  --z-sticky:       200;
  --z-fixed:        300;
  --z-tooltip:      500;
  --z-modal-bg:     900;
  --z-modal:        1000;
  --z-alert:        1100;
  --z-loader:       2000;
  --z-popover:      10000;
  --z-spotlight:    149000;
  --z-demo-bar:     149800;
  --z-beacon:       150000;
  --z-boot:         160000;  /* Cinematic boot sequence — above everything */
  --z-toast:        200000;  /* Always on top */
}
```

---

## Layout Constants

```css
:root {
  --sidebar-w:       240px;          /* Main navigation sidebar (slightly narrower than AEGIS) */
  --sidebar-w-mini:  56px;           /* Icon-only collapsed mode */
  --header-h:        52px;           /* Top bar height */
  --content-max:     1440px;         /* Max content width */

  /* Modal widths */
  --modal-sm:  420px;
  --modal-md:  620px;
  --modal-lg:  860px;
  --modal-xl:  1060px;
  --modal-full: calc(100vw - 64px);
}
```

---

## Component Library

### Buttons

```
Primary   — Accent blue background, white text. The one true CTA per page/section.
Secondary — White background, border, primary text. Most common.
Ghost     — No background or border, secondary text. Tertiary actions.
Danger    — Red. Destructive confirmations only.
Icon      — Square, icon only. Toolbar actions.

Sizes: xl (for landing/feature CTAs), lg (default forms), md (tables/toolbars), sm (inline), xs (badge actions)

Hover: Primary darkens. Secondary gets bg-elevated background.
Active (pressed): scale(0.97) — the Apple "press" micro-interaction.
Focus: 3px accent glow ring (--shadow-focus).
Disabled: 40% opacity, cursor not-allowed.
```

### Status Pills (Promotion Cycle)

The most critical UI component. Used everywhere on the main table:

```
Draft          — Indigo pill: #6366F1 bg-8%, indigo border-25%, indigo text
Authorized     — Amber pill:  #F59E0B bg-8%, amber border-25%, amber text
Master         — Emerald pill: #10B981 bg-8%, emerald border-25%, emerald text
Archived       — Slate pill:  #94A3B8 bg-8%, slate border-25%, slate text
Update Pending — Blue pill (accent) for in-progress authorization state
```

All pills: `border-radius: var(--r-full)`, `font-size: var(--font-xs)`, `font-weight: 600`, `letter-spacing: var(--tracking-wide)`, `padding: 2px 10px`.

### Three-State Boolean Cell

Used throughout the MCPT main table for checklist columns:

```
true  → ✓  — emerald green, --bool-true-bg background
false → ✗  — red, --bool-false-bg background
null  → —  — slate, --bool-null-bg background
```
Display: centered icon in a small rounded cell, 32×24px. Clicking cycles: null → true → false → null.

### Data Table

The hero component of the entire app. It must be world-class:

```
Header row:
  - bg-surface background
  - font-sm, weight-semibold, text-muted
  - Letter-spacing: tracking-wider, uppercase (Apple Numbers style)
  - 1px bottom border-emphasis
  - Sortable columns: sort icon appears on hover, rotates on sort

Body rows:
  - 44px row height (comfortable, Apple Tables density)
  - Hover: --table-row-hover (subtle blue tint)
  - Selected: --table-row-selected
  - 1px bottom border-muted separator
  - Inline edit: click cell → transforms to input with focus ring
  - Sticky first column (Diagram GUID / Level) on horizontal scroll
  - Sticky header on vertical scroll

Virtual scroll: render only visible rows for /get-mcpt which may return 500+ rows.

Column resize: drag handles on header borders (cursor: col-resize).
Column reorder: drag headers to rearrange.
Density toggle: Compact (32px) / Default (44px) / Spacious (56px).
```

### Cards

```
base: bg-surface, border-default 1px, radius-lg, shadow-sm
hover: shadow-md, bg-elevated (subtle lift)
active/selected: accent border-left 3px (like Notion)
metric card: large number (font-3xl, bold), label (font-xs, muted), trend indicator
```

### Modals

```
backdrop: rgba(15,23,42,0.4), blur(4px)
container: bg-base, shadow-2xl, radius-xl
header: sp-4 padding, text-primary font-lg bold, close button top-right
footer: border-top, action buttons right-aligned (cancel left, confirm right)
animation: scale(0.95)→scale(1) + opacity 0→1 over 200ms ease-out
```

### Toast Notifications

```
position: fixed, top-right, sp-4 from edges, z-toast
style: bg-surface, border-default, shadow-lg, radius-md
icon: colored by type (success/warning/error/info)
width: 320px
animation: slide in from right, fade out after 4 seconds
stack: multiple toasts stack vertically with sp-2 gap
```

### Inline Edit Pattern

When a user clicks an editable table cell:

```
1. Cell transforms: bg-input + border-focus + shadow-focus (no DOM height change)
2. User edits value
3. Blur or Enter: optimistic update → POST /edit-entry → confirm
4. ESC: revert to original value
5. Error: red flash + toast notification + revert
6. Visual: A "✏" pencil appears on hover over editable cells
```

---

## Navigation Architecture

### Top Header Bar (52px)

```
Left:   [MCPT Logo/Icon]  [App Name "MCPT"]  [Promotion Date Selector ▼]
Center: [current module title — fades in on navigate]
Right:  [Promotion Cycle Status Indicator]  [🔔 Notifications]  [User Initial Avatar]  [⚙ Settings]
```

The **Promotion Cycle Status Indicator** is a key "Apple" touch — a small pill in the header showing the current two-week cycle state (e.g., "Cycle 14 · Draft Phase") that links to the Authorization Dashboard.

### Left Sidebar (240px)

```
[MCPT wordmark]
─────────────────
CORE
  📋 MCPT Table
  ✅ Authorization
  📦 DSL Generator
─────────────────
REPORTS
  📅 Weekly Tasking
─────────────────
METRICS
  💰 Charging
  📊 NimbusBOE
  📄 DID Working
─────────────────
TOOLS
  ✓ PAL Checklist
  📚 PAL Helper
─────────────────
ADMIN
  ⚙ Admin Panel
─────────────────
  [? Help] ← links to help system
```

Active state: left 3px accent border + accent-light background + accent text color (exactly how Linear does it).

---

## Boot Sequence ("Mission Launch")

On first load (or Ctrl+Shift+R reload):

1. **0–200ms**: Dark overlay fades in (`--bg-base` dark)
2. **200–600ms**: MCPT icon/logo draws in with a subtle scale-up from 0.8 → 1.0
3. **600–900ms**: "MCPT" wordmark appears with letter-by-letter opacity cascade
4. **900–1200ms**: Subtitle "Model Change Package Tracker" slides up from -8px
5. **1200–1500ms**: Loading bar fills to 100% (simulated, actual data loads in background)
6. **1500–1800ms**: Boot overlay fades out (opacity 1 → 0), app fades in underneath

**No progress spinner. No loading text. Just motion and confidence.**

Duration total: ~1.8 seconds. Can be skipped by pressing any key.
Boot sequence only shows if app hasn't been used in this browser session.

---

## Cinematic Demo Mode

When a guided demo is playing:

```
Background: all non-demo-target elements dim to 60% opacity (not black overlay — subtler)
Spotlight: target element gets slight elevation + bright border (accent glow)
Demo bar: minimal bottom strip showing current demo name + step count + ■ stop button
Audio: Narration plays automatically. Volume slider in demo bar.
Speed: 0.75x, 1x, 1.5x, 2x multiplier
Navigation: << Previous step / Next step >> arrows when narration pauses
```

---

## Guide Beacon

```
Position: fixed, bottom-right, 24px inset, z-beacon
Appearance: 44px circle, --accent blue background, white "?" icon
Animation: Subtle radial pulse — outer ring expands 100%→150% and fades, every 3 seconds
On hover: scale(1.08), shadow increases
On click: Slides open the Help Panel from the right
Keyboard: Press F1 to toggle
```

---

## Help Panel (380px)

Slides in from right edge:

```
Header:
  [← Back] or section breadcrumb
  "Help & Guides" title
  [✕ Close]

Body:
  [Search help...] — real-time search across all help content
  ─────────────────
  "What is this section?"
  2-3 sentence description of current module
  ─────────────────
  "Key Actions"
  Quick-action chips (e.g., "Add Row", "Generate DSL", "Export Excel")
  ─────────────────
  "▶ Watch Demo"  ← primary CTA, launches guided demo
  "📖 Full Documentation" ← opens help docs panel
  ─────────────────
  "Pro Tips" — 2-3 power-user tips for current module
```

Animation: slides from `translateX(100%)` → `translateX(0)` over 300ms ease-out.
Backdrop: none (panel doesn't block app — user can still see the UI behind it).

---

## Accessibility

- All interactive elements: visible focus ring (--shadow-focus)
- Keyboard nav: Tab/Enter/Escape everywhere
- ARIA labels on all icon-only buttons
- Reduced motion: `@media (prefers-reduced-motion: reduce)` — all animations → instant
- Color contrast: All text meets WCAG AA (4.5:1 minimum)
- Screen reader: All status changes announced via aria-live regions
- Dark mode: `@media (prefers-color-scheme: dark)` auto-detection + manual toggle
- Flash prevention: Inline `<script>` in `<head>` sets theme before CSS loads (prevents FOUC)

---

## Inter Font Loading

```html
<!-- In <head>, preload for performance -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

If offline (corporate network blocks Google Fonts): Fall back to system fonts.
Ship Inter .woff2 files in `static/fonts/` as local backup:
- `Inter-Regular.woff2`
- `Inter-Medium.woff2`
- `Inter-SemiBold.woff2`
- `Inter-Bold.woff2`
