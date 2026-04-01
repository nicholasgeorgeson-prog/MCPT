# MCPT — Video Studio Specification (Module 16)

## Philosophy

One command. Zero paid services. Hands-off until review.

```bash
python video_studio/generate_all_videos.py
```

That is the entire user interaction. The system starts the app, seeds it with realistic
data, records every feature and sub-feature, applies professional post-processing,
generates narration, produces concept animations, assembles final MP4s, then launches
a review server at localhost:7777 where the user approves or re-queues each video.

Nobody sits at a desk. Nobody clicks anything. Nobody pays for a service.
When the user opens localhost:7777, the videos are done.

---

## What Makes These Videos Impressive

Corporate software demos are universally terrible — grainy screen recordings, inconsistent
cursor, no zoom, monotone narration, no concept explanations. MCPT videos will look like
Apple product launch demos applied to an engineering workflow tool.

The specific techniques that elevate this beyond anything in the corporate software space:

### 1. The Zoom-to-Element System
Before every interaction, the camera smoothly zooms into the target element — filling
~60% of the frame with just that UI element — pauses for the narration, then smoothly
zooms back out to show context. This is what professional screencam software (Camtasia,
ScreenFlow) does at $300/year. MCPT does it free, automated, per-element.

Implemented via OpenCV: Playwright captures element bounding box from JavaScript
(`getBoundingClientRect()`), then a smooth bicubic interpolation zooms into that region
over 20 frames (0.67 seconds at 30fps) using a cubic ease-in-out curve.

### 2. The Custom Recording Cursor
The default browser cursor is invisible in recordings. MCPT injects a custom 32px
blue circle cursor before recording begins. On hover: subtle glow. On click: bright
ripple pulse that expands from the click point and fades over 12 frames. On form focus:
cursor transforms into a thin vertical bar. This alone makes the videos look professional.

### 3. Manim Concept Animations
The promotion cycle, GUID/DSLID model, authorization workflow, and boolean states are
explained with Manim — the same engine behind 3Blue1Brown/Grant Sanderson animations.
These are 20–60 second mathematical-quality animated diagrams that NO competing corporate
engineering tool has ever shipped. Smooth morphing shapes, animated arrows, color-coded
state transitions, professional typography. This is the "wow" moment.

### 4. Animated Lower Thirds
Every scene starts with a module name + action label sliding up from the bottom
(news-broadcast style). The lower third is a translucent dark pill with the "Slate"
design language — "MCPT Table  ·  Adding a Diagram". It fades out after 2 seconds.
Generated with Pillow (no ImageMagick dependency) and composited via OpenCV.

### 5. Callout Arrows
When the narration references a specific UI element, an animated arrow pointing at that
element appears — drawn in the accent blue color with a pulsing glow, extending from
outside the element toward its center. Not a static arrow — it animates in (growing from
its origin point) over 10 frames. This is what SaaS product tutorials use, and it looks
professional every single time.

### 6. Cross-Dissolve Transitions
Between scenes within a module: 15-frame (0.5s) cross-dissolve. Between modules:
20-frame fade-to-black and fade-in. All done with OpenCV addWeighted, zero cost.

### 7. The Review Interface
After generation completes, a minimal Flask server opens at localhost:7777 showing:
- All videos organized by module and sub-feature
- Each video plays inline with a HTML5 player
- "Approve ✓" / "Needs Retake ↺" / "Reject ✕" buttons
- Global progress: "46/51 approved"
- Re-queue button: marks a video for regeneration, runs on next `--pending` pass
- Export manifest: writes final `manifest.json` with only approved videos

---

## Complete File Structure

```
video_studio/
├── generate_all_videos.py          ← THE ONE COMMAND
├── config.py                       ← Resolution, FPS, quality, app URL
├── requirements_video.txt          ← Additional packages (manim, moviepy, etc.)
│
├── core/
│   ├── app_controller.py           ← Start/stop MCPT, health poll
│   ├── test_data_seeder.py         ← Seed realistic demo data via API
│   └── video_manifest.py           ← Read/write manifest.json
│
├── scenes/                         ← ALL demo definitions (the script)
│   ├── __init__.py
│   ├── base_scene.py               ← Scene dataclass + validation
│   ├── module_01_mcpt_table.py
│   ├── module_02_auth_dashboard.py
│   ├── module_03_dsl_generator.py
│   ├── module_04_weekly_tasking.py
│   ├── module_05_charging.py
│   ├── module_06_boe.py
│   ├── module_07_did_working.py
│   ├── module_08_pal_checklist.py
│   ├── module_09_pal_helper.py
│   ├── module_10_admin_panel.py
│   ├── module_11_notifications.py
│   └── concept_scenes.py           ← Manim concept animation scripts
│
├── recorder/
│   ├── playwright_recorder.py      ← Drives MCPT UI, captures WebM
│   ├── cursor_injector.py          ← Injects custom cursor CSS+JS
│   └── element_locator.py          ← getBoundingClientRect per selector
│
├── enhancer/
│   ├── pipeline.py                 ← Orchestrates all enhancement steps
│   ├── webm_to_mp4.py              ← FFmpeg: WebM→H.264 MP4, CRF 18
│   ├── zoom_controller.py          ← Smooth zoom-to-element (OpenCV)
│   ├── cursor_overlay.py           ← Draw custom cursor + click ripples
│   ├── callout_renderer.py         ← Animated arrows + glow circles
│   ├── lower_third.py              ← Pillow: title cards, lower thirds
│   └── transition_renderer.py      ← Cross-dissolve, fade-to-black
│
├── audio/
│   ├── narration_generator.py      ← edge-tts → MP3 (free, offline-capable)
│   └── audio_assembler.py          ← FFmpeg: mix narration + video timing
│
├── manim_scenes/
│   ├── promotion_cycle.py          ← Draft→Authorized→Master animated timeline
│   ├── guid_dslid_model.py         ← Three-identifier animated diagram
│   ├── bool_states.py              ← Null/True/False cycling animation
│   ├── auth_workflow.py            ← Authorization sign-off flow
│   ├── dsl_file_structure.py       ← ZIP expanding to show 5 category files
│   └── manim_runner.py             ← Subprocess wrapper + fallback check
│
├── assembler/
│   ├── video_assembler.py          ← FFmpeg: concat segments + mix audio
│   └── chapter_writer.py           ← Write FFmpeg chapter metadata
│
└── review/
    ├── review_server.py            ← Flask app on port 7777
    └── templates/
        └── review.html             ← Video review interface
```

Output:
```
static/videos/
├── manifest.json
├── concepts/
│   ├── promotion_cycle.mp4         (45s Manim animation)
│   ├── guid_dslid_model.mp4        (60s Manim animation)
│   ├── bool_states.mp4             (25s Manim animation)
│   ├── auth_workflow.mp4           (40s Manim animation)
│   └── dsl_file_structure.mp4      (30s Manim animation)
└── modules/
    ├── mcpt_table/
    │   ├── overview.mp4            (3 min — full module walkthrough)
    │   ├── add_diagram.mp4         (75s — adding a new entry)
    │   ├── inline_editing.mp4      (60s — editing fields in table)
    │   ├── bool_editing.mp4        (45s — cycling three-state checkboxes)
    │   ├── filtering.mp4           (60s — filtering and searching)
    │   ├── promotion_filter.mp4    (45s — switching promotion dates)
    │   └── archiving.mp4           (40s — archiving a row)
    ├── auth_dashboard/
    │   ├── overview.mp4
    │   ├── email_authorizers.mp4
    │   └── progress_tracking.mp4
    ├── dsl_generator/
    │   ├── overview.mp4
    │   ├── download_zip.mp4
    │   └── category_files.mp4
    ├── weekly_tasking/
    │   ├── overview.mp4
    │   ├── submit_tasks.mp4
    │   ├── director_view.mp4
    │   └── export_word.mp4
    ├── charging/
    │   ├── overview.mp4
    │   ├── upload_sap.mp4
    │   └── pivot_table.mp4
    ├── boe/
    │   ├── overview.mp4
    │   ├── monthly_summary.mp4
    │   └── by_supp_code.mp4
    ├── did_working/
    │   ├── overview.mp4
    │   ├── contract_pivot.mp4
    │   ├── function_pivot.mp4
    │   ├── gap_analysis.mp4
    │   └── raw_data_view.mp4
    ├── pal_checklist/
    │   ├── overview.mp4
    │   ├── checking_items.mp4
    │   └── export_checklist.mp4
    ├── pal_helper/
    │   ├── overview.mp4
    │   └── browse_discipline.mp4
    ├── admin_panel/
    │   ├── overview.mp4
    │   ├── system_settings.mp4
    │   ├── trb_chair.mp4
    │   ├── email_config.mp4
    │   └── manage_dropdowns.mp4
    └── notifications/
        ├── overview.mp4
        └── notification_feed.mp4
```

Total: ~51 videos, ~65 minutes of content.

---

## Video Specifications

```python
# config.py
VIDEO_CONFIG = {
    'width':         1280,
    'height':        720,
    'fps':           30,
    'crf':           18,          # H.264 quality (0=lossless, 23=default, 51=worst)
    'preset':        'slow',      # FFmpeg x264 preset (slow = better compression)
    'app_url':       'http://localhost:5060',
    'app_startup_timeout': 30,    # seconds to wait for Flask to be ready
    'narration_rate':'-8%',       # edge-tts speed adjustment
    'narration_voice':'en-US-AvaNeural',
    'zoom_duration_frames':  20,  # frames to zoom in/out (0.67s at 30fps)
    'zoom_scale':           1.6,  # how much to zoom in (1.6x = 60% of frame)
    'transition_frames':    15,   # cross-dissolve duration
    'lower_third_duration': 2.0,  # seconds lower third stays visible
    'callout_arrow_frames': 10,   # arrow animation duration
    'cursor_size':          28,   # custom cursor diameter (px)
    'cursor_color':    (37, 99, 235),     # --accent blue (BGR for OpenCV)
    'callout_color':   (37, 99, 235),     # callout arrow color
    'output_dir':      'static/videos',
}
```

---

## generate_all_videos.py — The One Command

```python
"""
MCPT Video Studio — Master Generator
Usage:
    python generate_all_videos.py                    # Generate all videos
    python generate_all_videos.py --module mcpt_table # One module only
    python generate_all_videos.py --concepts-only     # Manim animations only
    python generate_all_videos.py --demos-only        # Playwright demos only
    python generate_all_videos.py --force             # Regenerate all (skip cache)
    python generate_all_videos.py --pending           # Re-run rejected/retake videos
    python generate_all_videos.py --no-review         # Skip review server at end
    python generate_all_videos.py --review-only       # Just open review server
"""

import argparse, sys, time, subprocess
from pathlib import Path
from core.app_controller import MCPTAppController
from core.test_data_seeder import seed_demo_data
from manim_scenes.manim_runner import generate_concept_videos
from recorder.playwright_recorder import record_all_modules
from enhancer.pipeline import enhance_all_recordings
from audio.narration_generator import generate_all_narration
from assembler.video_assembler import assemble_all_videos
from core.video_manifest import write_manifest
from review.review_server import start_review_server

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', help='Generate only this module')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--concepts-only', action='store_true')
    parser.add_argument('--demos-only', action='store_true')
    parser.add_argument('--pending', action='store_true')
    parser.add_argument('--no-review', action='store_true')
    parser.add_argument('--review-only', action='store_true')
    args = parser.parse_args()

    print("\n" + "═"*60)
    print("  MCPT Video Studio")
    print("  Automated Demo Video Generation Pipeline")
    print("═"*60 + "\n")

    if args.review_only:
        start_review_server(port=7777, open_browser=True)
        return

    # Step 1: Start MCPT app
    print("[1/7] Starting MCPT application...")
    controller = MCPTAppController(app_url='http://localhost:5060')
    was_already_running = controller.is_running()
    if not was_already_running:
        controller.start()
        controller.wait_until_ready(timeout=30)
    print("      ✓ MCPT ready\n")

    # Step 2: Seed demo data
    print("[2/7] Seeding demo data...")
    seed_demo_data(app_url='http://localhost:5060', force=args.force)
    print("      ✓ Demo data ready\n")

    # Step 3: Generate concept animations (Manim)
    if not args.demos_only:
        print("[3/7] Generating concept animations (Manim)...")
        generate_concept_videos(force=args.force)
        print("      ✓ Concept animations done\n")
    else:
        print("[3/7] Skipping concept animations (--demos-only)\n")

    # Step 4: Record Playwright demos
    if not args.concepts_only:
        print("[4/7] Recording live demo videos...")
        record_all_modules(
            module_filter=args.module,
            force=args.force,
            pending_only=args.pending
        )
        print("      ✓ All recordings captured\n")

    # Step 5: Generate narration audio
    print("[5/7] Generating narration audio (edge-tts)...")
    generate_all_narration(force=args.force)
    print("      ✓ Narration audio ready\n")

    # Step 6: Enhance and assemble
    print("[6/7] Enhancing videos + assembling final MP4s...")
    print("      (zoom effects, callouts, lower thirds, transitions, audio mix)")
    assemble_all_videos(force=args.force)
    print("      ✓ All videos assembled\n")

    # Step 7: Write manifest
    print("[7/7] Writing video manifest...")
    write_manifest('static/videos/manifest.json')
    count = len(list(Path('static/videos').rglob('*.mp4')))
    print(f"      ✓ manifest.json written — {count} videos ready\n")

    # Stop app if we started it
    if not was_already_running:
        controller.stop()

    # Summary
    print("═"*60)
    print(f"  ✓  Generation complete — {count} videos produced")
    print(f"  ✓  Output: static/videos/")
    if not args.no_review:
        print(f"  →  Opening review interface at http://localhost:7777")
        print("═"*60 + "\n")
        start_review_server(port=7777, open_browser=True)
    else:
        print("═"*60 + "\n")

if __name__ == '__main__':
    main()
```

---

## Scene Definition Format

Every scene in every module is defined as a Python dataclass. This separates
"what to do" from "how to record it" — clean, testable, extensible.

```python
# scenes/base_scene.py
from dataclasses import dataclass, field
from typing import Optional, List, Callable

@dataclass
class DemoStep:
    """One narrated action in a demo video."""
    narration:       str              # Text for TTS + subtitles
    target_selector: Optional[str]   # CSS selector of element to zoom to
    action:          Optional[str]   # 'click', 'type', 'hover', 'scroll', 'wait'
    action_value:    Optional[str]   # For 'type': text to type
    pause_before:    float = 0.5     # seconds to pause before action
    pause_after:     float = 1.0     # seconds to hold after action
    zoom_in:         bool  = True    # zoom to element before action
    show_callout:    bool  = True    # show callout arrow pointing to element
    callout_label:   Optional[str] = None   # label next to callout
    playwright_fn:   Optional[Callable] = None  # custom Playwright code

@dataclass
class SubDemo:
    """A focused walkthrough of one sub-feature."""
    id:          str
    title:       str
    description: str
    icon:        str              # Lucide icon name
    steps:       List[DemoStep]
    pre_action:  Optional[Callable] = None  # run before recording starts

@dataclass
class ModuleDemo:
    """Complete demo definition for one module."""
    module_id:    str
    module_title: str
    navigate_to:  str             # sidebar nav selector or URL fragment
    overview:     List[DemoStep]  # full module walkthrough
    sub_demos:    List[SubDemo]   # individual feature deep-dives
```

---

## Module Scene Definitions (All 13 Modules)

### Module 1 — MCPT Main Table (scenes/module_01_mcpt_table.py)

```python
MODULE_01 = ModuleDemo(
    module_id='mcpt_table',
    module_title='MCPT Main Table',
    navigate_to='#nav-mcpt-table',
    overview=[
        DemoStep(
            narration="Welcome to the MCPT Main Table — the central workspace for managing diagram promotions. Every diagram in the current two-week cycle is listed here with all 49 tracking fields visible.",
            target_selector='.mcpt-data-grid',
            action='wait', pause_after=2.0
        ),
        DemoStep(
            narration="At the top of the header, the promotion date selector controls which cycle you are viewing. Click the dropdown to switch between cycles without reloading the page.",
            target_selector='.promotion-date-selector',
            action='click', pause_after=1.5,
            callout_label="Promotion Date"
        ),
        DemoStep(
            narration="Each row is a diagram. The Level column shows the hierarchy number — count the dots in the level string and add one. A 'Draft Copy' suffix means this is the editable draft version.",
            target_selector='.col-level',
            action='hover', pause_after=2.0,
            callout_label="Level Number"
        ),
        DemoStep(
            narration="The checklist columns use a three-state system. Green check means complete, red X means incomplete, and a dash means not applicable. Click any cell to cycle through all three states.",
            target_selector='.bool-cell:first-child',
            action='hover', pause_after=2.5,
            callout_label="Three-State Boolean"
        ),
        DemoStep(
            narration="The Status column shows where each diagram is in the authorization workflow — Draft, Update Pending, or Authorized. This drives the Authorization Dashboard.",
            target_selector='.col-authorization',
            action='hover', pause_after=2.0
        ),
    ],
    sub_demos=[
        SubDemo(
            id='add_diagram', title='Adding a Diagram', icon='plus-circle',
            description='Add a new diagram entry to the current promotion cycle',
            steps=[
                DemoStep(narration="To add a new diagram, click the Add Row button in the toolbar. A form will open where you enter the required details.", target_selector='.add-row-btn', action='click', pause_after=0.8, callout_label="Add Row"),
                DemoStep(narration="Enter the diagram GUID — this is the permanent identifier shared between the Draft and Master versions of the diagram.", target_selector='#add-guid-input', action='type', action_value='9820E23DD3204072819C50B7A2E57093', pause_after=0.5),
                DemoStep(narration="Select the diagram category from the dropdown. Categories control which DSL batch file this diagram will appear in during promotion.", target_selector='#add-category-select', action='click', pause_after=1.0, callout_label="Category"),
                DemoStep(narration="Enter the Model Change Package title — this is the human-readable description that will appear in authorization emails and reports.", target_selector='#add-title-input', action='type', action_value='Update Process Flow Section 1.3.8', pause_after=0.5),
                DemoStep(narration="Click Add Entry to submit. The entry posts to the backend API and appears in the table immediately.", target_selector='#add-entry-submit', action='click', pause_after=2.0, callout_label="Submit"),
            ]
        ),
        SubDemo(
            id='inline_editing', title='Inline Editing', icon='edit-2',
            description='Edit any field directly in the table without opening a modal',
            steps=[
                DemoStep(narration="Editable cells show a pencil icon when you hover over them. Click any editable cell to enter edit mode.", target_selector='.editable-cell:first-of-type', action='hover', pause_after=1.0, callout_label="Hover to reveal edit"),
                DemoStep(narration="The cell transforms into an input field with a focus ring. Type your new value here.", target_selector='.editable-cell:first-of-type', action='click', pause_after=0.5),
                DemoStep(narration="Press Enter to save, or Escape to cancel. The change is sent to the API using the exact field name from the API response.", target_selector='.inline-edit-input', action='type', action_value='Updated notes text', pause_after=0.5),
            ]
        ),
        SubDemo(
            id='bool_cycling', title='Three-State Boolean Fields', icon='check-square',
            description='How the three-state checklist system works',
            steps=[
                DemoStep(narration="Boolean fields have three states — not just true and false. A dash means the status is unknown or not applicable.", target_selector='.bool-cell.bool-null', action='hover', pause_after=1.5, callout_label="Unknown / N/A"),
                DemoStep(narration="Click once to mark it complete. The cell turns green.", target_selector='.bool-cell.bool-null', action='click', pause_after=1.0),
                DemoStep(narration="Click again to mark it incomplete. The cell turns red.", target_selector='.bool-cell.bool-true', action='click', pause_after=1.0),
                DemoStep(narration="One more click returns it to the unknown state. The cycle continues: dash, check, X, dash.", target_selector='.bool-cell.bool-false', action='click', pause_after=1.5),
            ]
        ),
        SubDemo(
            id='filtering', title='Filtering & Searching', icon='filter',
            description='Find specific diagrams quickly',
            steps=[
                DemoStep(narration="The global search box filters across all columns in real time. Type a level number or keyword to narrow the list instantly.", target_selector='.table-search-input', action='type', action_value='1.3.8', pause_after=1.5, callout_label="Global Search"),
                DemoStep(narration="Column filters let you drill deeper. Click the filter icon on any column header to see available values.", target_selector='.col-filter-btn', action='click', pause_after=1.0),
                DemoStep(narration="Use the Status filter to show only diagrams that are pending authorization. This quickly surfaces who needs to take action.", target_selector='.filter-option-update-pending', action='click', pause_after=2.0, callout_label="Status Filter"),
            ]
        ),
        SubDemo(
            id='promotion_date', title='Switching Promotion Cycles', icon='calendar',
            description='Navigate between two-week promotion cycles',
            steps=[
                DemoStep(narration="The promotion date selector in the header controls the entire table view. Click it to see all available promotion cycles.", target_selector='.promotion-date-selector', action='click', pause_after=1.0),
                DemoStep(narration="Select a previous cycle to see a historical snapshot. All filtering and views work the same for past cycles.", target_selector='.promotion-date-option:nth-child(2)', action='click', pause_after=1.5),
                DemoStep(narration="Your selection is saved in the browser. Next time you open MCPT, you will return to the same cycle.", target_selector='.mcpt-data-grid', action='wait', pause_after=2.0),
            ]
        ),
    ]
)
```

*(Define equivalent scene files for all 12 remaining modules following this exact pattern.)*

---

## Custom Cursor Injector (recorder/cursor_injector.py)

```python
CURSOR_CSS = """
#mcpt-recording-cursor {
    position: fixed;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(37, 99, 235, 0.85);
    border: 2.5px solid rgba(255, 255, 255, 0.9);
    pointer-events: none;
    z-index: 2147483647;
    transform: translate(-50%, -50%);
    transition: transform 80ms cubic-bezier(0, 0, 0.2, 1),
                width 80ms ease, height 80ms ease,
                background 80ms ease;
    box-shadow: 0 2px 8px rgba(37,99,235,0.4), 0 0 0 0 rgba(37,99,235,0.3);
    will-change: left, top;
}
#mcpt-recording-cursor.clicking {
    transform: translate(-50%, -50%) scale(0.85);
    background: rgba(29, 78, 216, 0.95);
}
.mcpt-ripple {
    position: fixed;
    border-radius: 50%;
    border: 2px solid rgba(37, 99, 235, 0.7);
    pointer-events: none;
    z-index: 2147483646;
    animation: mcpt-ripple-anim 0.45s cubic-bezier(0, 0, 0.2, 1) forwards;
}
@keyframes mcpt-ripple-anim {
    0%   { width: 28px; height: 28px; opacity: 0.8; margin: -14px 0 0 -14px; }
    100% { width: 72px; height: 72px; opacity: 0;   margin: -36px 0 0 -36px; }
}
"""

CURSOR_JS = """
(function() {
    // Create cursor
    const cur = document.createElement('div');
    cur.id = 'mcpt-recording-cursor';
    document.body.appendChild(cur);

    // Track position
    document.addEventListener('mousemove', e => {
        cur.style.left = e.clientX + 'px';
        cur.style.top  = e.clientY + 'px';
    }, { passive: true });

    // Click ripple
    document.addEventListener('mousedown', e => {
        cur.classList.add('clicking');
        const ripple = document.createElement('div');
        ripple.className = 'mcpt-ripple';
        ripple.style.left = e.clientX + 'px';
        ripple.style.top  = e.clientY + 'px';
        document.body.appendChild(ripple);
        setTimeout(() => ripple.remove(), 500);
    });
    document.addEventListener('mouseup', () => cur.classList.remove('clicking'));

    // Hide native cursor
    document.documentElement.style.cursor = 'none';
    document.querySelectorAll('*').forEach(el => {
        const c = window.getComputedStyle(el).cursor;
        if (c && c !== 'none') el.style.cursor = 'none';
    });
})();
"""

async def inject_cursor(page):
    """Inject the custom recording cursor into the page."""
    await page.add_style_tag(content=CURSOR_CSS)
    await page.evaluate(CURSOR_JS)
```

---

## Zoom Controller (enhancer/zoom_controller.py)

```python
import cv2, numpy as np

def smooth_zoom_frames(frames, bbox, config, direction='in'):
    """
    Smoothly zoom toward a bounding box over N frames.
    bbox: (x, y, width, height) in pixel coordinates
    direction: 'in' zooms toward bbox, 'out' zooms back to full frame
    Returns: list of enhanced frames
    """
    n_frames = config['zoom_duration_frames']
    target_scale = config['zoom_scale']
    H, W = frames[0].shape[:2]

    cx = bbox[0] + bbox[2] // 2
    cy = bbox[1] + bbox[3] // 2

    result = []
    for i, frame in enumerate(frames):
        # Cubic ease in-out: t goes 0→1 (zoom in) or 1→0 (zoom out)
        t_linear = i / max(n_frames - 1, 1)
        t = t_linear * t_linear * (3 - 2 * t_linear)  # smoothstep
        scale = 1 + (target_scale - 1) * (t if direction == 'in' else 1 - t)

        # Compute crop window centered on element
        new_w = int(W / scale)
        new_h = int(H / scale)
        x1 = max(0, min(cx - new_w // 2, W - new_w))
        y1 = max(0, min(cy - new_h // 2, H - new_h))
        x2, y2 = x1 + new_w, y1 + new_h

        cropped = frame[y1:y2, x1:x2]
        zoomed  = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_CUBIC)
        result.append(zoomed)

    return result


def apply_zoom_sequence(all_frames, zoom_events, config):
    """
    Given a list of (frame_idx, bbox) zoom events, apply smooth
    zoom-in before the event and zoom-out after.
    """
    out = list(all_frames)  # copy
    n = config['zoom_duration_frames']

    for frame_idx, bbox in zoom_events:
        # Zoom in: frames leading up to event
        start = max(0, frame_idx - n)
        in_frames = smooth_zoom_frames(all_frames[start:frame_idx], bbox, config, 'in')
        out[start:frame_idx] = in_frames

        # Hold zoomed for the action duration (next 45 frames = 1.5s)
        hold_end = min(len(all_frames), frame_idx + 45)
        for j in range(frame_idx, hold_end):
            H, W = all_frames[j].shape[:2]
            scale = config['zoom_scale']
            cx = bbox[0] + bbox[2] // 2
            cy = bbox[1] + bbox[3] // 2
            new_w, new_h = int(W / scale), int(H / scale)
            x1 = max(0, min(cx - new_w // 2, W - new_w))
            y1 = max(0, min(cy - new_h // 2, H - new_h))
            cropped = all_frames[j][y1:y1+new_h, x1:x1+new_w]
            out[j] = cv2.resize(cropped, (W, H), interpolation=cv2.INTER_CUBIC)

        # Zoom out after hold
        end = min(len(all_frames), hold_end + n)
        out_frames = smooth_zoom_frames(all_frames[hold_end:end], bbox, config, 'out')
        out[hold_end:end] = out_frames

    return out
```

---

## Callout Renderer (enhancer/callout_renderer.py)

```python
import cv2, numpy as np, math

def draw_callout_arrow(frame, target_bbox, config, frame_progress):
    """
    Draw an animated arrow pointing at target_bbox.
    frame_progress: 0.0–1.0 (0=not yet started, 1=fully drawn)
    The arrow grows from its origin toward the target over the animation.
    """
    if frame_progress <= 0:
        return frame

    H, W = frame.shape[:2]
    tx = target_bbox[0] + target_bbox[2] // 2  # target center x
    ty = target_bbox[1] + target_bbox[3] // 2  # target center y

    # Arrow starts 80px away at 45° angle from target
    angle = math.pi * 0.75  # 135 degrees = upper-left approach
    dist = 80
    sx = int(tx + math.cos(angle) * dist)  # start x
    sy = int(ty + math.sin(angle) * dist)  # start y

    # Current endpoint based on progress
    ex = int(sx + (tx - sx) * frame_progress)
    ey = int(sy + (ty - sy) * frame_progress)

    color = config['callout_color']  # (37, 99, 235) blue
    thickness = 3
    overlay = frame.copy()

    # Draw arrow line with glow (draw thicker+transparent then thinner+opaque)
    cv2.line(overlay, (sx, sy), (ex, ey), color, thickness + 4)
    alpha_layer = cv2.addWeighted(overlay, 0.3, frame, 0.7, 0)
    cv2.line(alpha_layer, (sx, sy), (ex, ey), color, thickness)

    # Arrowhead only when fully drawn
    if frame_progress > 0.85:
        alpha2 = (frame_progress - 0.85) / 0.15
        cv2.arrowedLine(alpha_layer, (sx, sy), (ex, ey), color, thickness,
                        tipLength=0.25 * alpha2)

    # Pulsing circle at target when fully drawn
    if frame_progress >= 1.0:
        pulse = 0.5 + 0.5 * math.sin(frame_progress * math.pi * 6)
        radius = int(target_bbox[2] // 2 + 8 + 4 * pulse)
        glow = frame.copy()
        cv2.circle(glow, (tx, ty), radius + 4, color, 2)
        alpha_layer = cv2.addWeighted(glow, 0.3, alpha_layer, 0.7, 0)
        cv2.circle(alpha_layer, (tx, ty), radius, color, 2)

    return alpha_layer
```

---

## Lower Third Renderer (enhancer/lower_third.py)

```python
from PIL import Image, ImageDraw, ImageFont
import numpy as np, cv2

def render_lower_third(frame, module_title, action_title, progress, config):
    """
    Render an animated lower third onto a video frame.
    progress: 0.0 = fully hidden (below frame), 1.0 = fully visible
    Slides UP from below: translateY from +80px to 0px
    Fades in simultaneously (opacity 0→1)
    """
    H, W = frame.shape[:2]
    pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil)

    # Smoothstep progress
    t = progress * progress * (3 - 2 * progress)
    slide_offset = int((1 - t) * 80)
    alpha = t

    # Lower third area: bottom 80px of frame
    pill_h  = 52
    pill_y  = H - 72 + slide_offset
    pill_x  = 32
    pill_w  = 480
    radius  = 12

    # Draw rounded pill background (dark translucent)
    pill_layer = Image.new('RGBA', pil.size, (0, 0, 0, 0))
    pill_draw  = ImageDraw.Draw(pill_layer)
    pill_color = (15, 23, 42, int(210 * alpha))  # --bg-base dark, ~82% opacity
    pill_draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + pill_w, pill_y + pill_h],
        radius=radius, fill=pill_color
    )

    # Module title (smaller, muted)
    font_sm = _get_font('Inter-Medium.ttf', 11)
    font_lg = _get_font('Inter-SemiBold.ttf', 15)
    accent  = (96, 165, 250, int(255 * alpha))   # --accent blue, bright
    white   = (241, 245, 249, int(255 * alpha))  # --text-primary light

    pill_draw.text((pill_x + 16, pill_y + 10), module_title.upper(),
                   font=font_sm, fill=accent)
    pill_draw.text((pill_x + 16, pill_y + 27), action_title,
                   font=font_lg, fill=white)

    # Accent left border
    pill_draw.rounded_rectangle(
        [pill_x, pill_y, pill_x + 3, pill_y + pill_h],
        radius=radius, fill=(37, 99, 235, int(255 * alpha))
    )

    pil_rgba = pil.convert('RGBA')
    pil_rgba = Image.alpha_composite(pil_rgba, pill_layer)
    return cv2.cvtColor(np.array(pil_rgba.convert('RGB')), cv2.COLOR_RGB2BGR)


def _get_font(filename, size):
    try:
        return ImageFont.truetype(f'static/fonts/{filename}', size)
    except Exception:
        return ImageFont.load_default()
```

---

## Manim Concept Animations (manim_scenes/)

### The Promotion Cycle (manim_scenes/promotion_cycle.py)

```python
from manim import *

class PromotionCycle(Scene):
    """
    45-second animated diagram showing the two-week promotion cycle.
    Draft → Authorized → Master with color-coded state transitions,
    timing arrows, and animated checklist completion.
    """
    def construct(self):
        # Color palette matches MCPT "Slate" design
        DRAFT_COLOR      = "#6366F1"   # --status-draft indigo
        AUTH_COLOR       = "#F59E0B"   # --status-authorized amber
        MASTER_COLOR     = "#10B981"   # --status-master emerald
        BG_COLOR         = "#0F172A"   # --bg-base dark
        TEXT_COLOR       = "#F1F5F9"   # --text-primary
        MUTED_COLOR      = "#94A3B8"   # --text-muted

        self.camera.background_color = BG_COLOR

        # Title
        title = Text("The Two-Week Promotion Cycle",
                     color=TEXT_COLOR, font="Inter", font_size=32, weight=BOLD)
        title.to_edge(UP, buff=0.5)
        self.play(FadeIn(title, shift=DOWN * 0.3), run_time=0.6)

        # Three state circles
        draft_circle  = Circle(radius=0.9, color=DRAFT_COLOR,  fill_opacity=0.15, stroke_width=3)
        auth_circle   = Circle(radius=0.9, color=AUTH_COLOR,   fill_opacity=0.15, stroke_width=3)
        master_circle = Circle(radius=0.9, color=MASTER_COLOR, fill_opacity=0.15, stroke_width=3)

        draft_circle.move_to(LEFT * 4)
        auth_circle.move_to(ORIGIN)
        master_circle.move_to(RIGHT * 4)

        draft_label  = Text("Draft",      color=DRAFT_COLOR,  font="Inter", font_size=20, weight=SEMIBOLD)
        auth_label   = Text("Authorized", color=AUTH_COLOR,   font="Inter", font_size=20, weight=SEMIBOLD)
        master_label = Text("Master",     color=MASTER_COLOR, font="Inter", font_size=20, weight=SEMIBOLD)

        draft_label.move_to(draft_circle)
        auth_label.move_to(auth_circle)
        master_label.move_to(master_circle)

        # Animate circles appearing
        self.play(
            GrowFromCenter(draft_circle), FadeIn(draft_label),
            run_time=0.8
        )
        self.wait(0.3)

        # Arrow: Draft → Authorized
        arrow1 = Arrow(draft_circle.get_right(), auth_circle.get_left(),
                       color=AUTH_COLOR, buff=0.1, stroke_width=3)
        arrow1_label = Text("Sign-off obtained",
                            color=MUTED_COLOR, font="Inter", font_size=12)
        arrow1_label.next_to(arrow1, UP, buff=0.15)

        self.play(
            GrowFromCenter(auth_circle), FadeIn(auth_label),
            GrowArrow(arrow1), FadeIn(arrow1_label),
            run_time=1.0
        )
        self.wait(0.3)

        # Arrow: Authorized → Master
        arrow2 = Arrow(auth_circle.get_right(), master_circle.get_left(),
                       color=MASTER_COLOR, buff=0.1, stroke_width=3)
        arrow2_label = Text("Promoted in Nimbus",
                            color=MUTED_COLOR, font="Inter", font_size=12)
        arrow2_label.next_to(arrow2, UP, buff=0.15)

        self.play(
            GrowFromCenter(master_circle), FadeIn(master_label),
            GrowArrow(arrow2), FadeIn(arrow2_label),
            run_time=1.0
        )

        self.wait(0.5)

        # Two-week timeline
        timeline = NumberLine(
            x_range=[0, 14, 1], length=10, include_numbers=False,
            color=MUTED_COLOR
        )
        timeline.to_edge(DOWN, buff=1.5)
        day_label = Text("Day 1", color=MUTED_COLOR, font="Inter", font_size=11)
        day_label.next_to(timeline.get_left(), DOWN, buff=0.15)
        end_label = Text("Day 14", color=MUTED_COLOR, font="Inter", font_size=11)
        end_label.next_to(timeline.get_right(), DOWN, buff=0.15)

        self.play(Create(timeline), FadeIn(day_label), FadeIn(end_label), run_time=0.8)

        # Animate a dot moving along the timeline
        dot = Dot(timeline.n2p(0), color=DRAFT_COLOR, radius=0.12)
        self.play(FadeIn(dot))
        self.play(dot.animate.move_to(timeline.n2p(7)),
                  dot.animate.set_color(AUTH_COLOR), run_time=1.5,
                  rate_func=smooth)
        self.play(dot.animate.move_to(timeline.n2p(14)),
                  dot.animate.set_color(MASTER_COLOR), run_time=1.2,
                  rate_func=smooth)

        self.wait(1.0)
        self.play(FadeOut(Group(*self.mobjects), shift=UP * 0.3), run_time=0.8)
```

*(Define equivalent Manim scenes for GUID/DSLID model, three-state booleans, authorization workflow, and DSL file structure.)*

---

## Review Server (review/review_server.py)

```python
"""
Lightweight review interface. Opens at localhost:7777 after generation.
User approves or marks videos for retake. Status saved to manifest.json.
"""
from flask import Flask, render_template, request, jsonify, send_from_directory
import json, webbrowser, threading
from pathlib import Path

review_app = Flask(__name__, template_folder='templates')
MANIFEST_PATH = Path('static/videos/manifest.json')

@review_app.route('/')
def index():
    manifest = json.loads(MANIFEST_PATH.read_text())
    return render_template('review.html', manifest=manifest)

@review_app.route('/api/review/status', methods=['POST'])
def update_status():
    data = request.json  # {"video_id": "...", "status": "approved|retake|rejected"}
    manifest = json.loads(MANIFEST_PATH.read_text())
    for section in manifest['videos'].values():
        for video in section:
            if video['id'] == data['video_id']:
                video['review_status'] = data['status']
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    return jsonify({'ok': True})

@review_app.route('/static/videos/<path:filename>')
def serve_video(filename):
    return send_from_directory('static/videos', filename)

def start_review_server(port=7777, open_browser=True):
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f'http://localhost:{port}')).start()
    review_app.run(port=port, debug=False)
```

The review HTML (`review/templates/review.html`) uses the same Slate design system as the main app:
- Left sidebar: module list with approved/total counts and color-coded status
- Main area: selected module's videos in a grid
- Each video card: HTML5 `<video>` player, title, duration, approve/retake/reject buttons
- Global stats bar at top: "46 / 51 approved — 3 need retake — 2 rejected"
- "Re-run pending" button calls `generate_all_videos.py --pending`

---

## Test Data Seeder (core/test_data_seeder.py)

Seeds the MCPT app with realistic demo data before recording begins.
Uses the same API endpoints the real app uses — not direct DB manipulation.

```python
DEMO_DIAGRAMS = [
    {
        "guid":                    "9820E23DD3204072819C50B7A2E57093",
        "diagramCategory":         "PromotionEngineeringApproved",
        "modelChangePackageTitle": "Update System Architecture Process Flow",
        "trbTitle":                "NAT-2026-14",
        "natContact":              "demo.user",
        "diagramLevel":            "1.3.8 Draft Copy",
        "Authorization":           "Update Pending",
        "Authorizer":              "Smith, John",
        "spFolderCreated":         True,
        "toolEntryCreated":        True,
        "relatedFilesPosted":      None,   # Unknown — shows dash
        "crPackageReady":          False,
        "notes":                   "Demo entry for video recording",
    },
    # ... 8–12 more entries covering all states (null/true/false booleans,
    # all category types, multiple authorizers, mix of Draft/Authorized/Master)
]

async def seed_demo_data(app_url, force=False):
    """POST demo entries to /api/mcpt/add-entry. Skip if already seeded."""
    # Check if already seeded (look for demo GUID in current data)
    # POST each entry
    # Set current promotion date to today's cycle
```

---

## Requirements (requirements_video.txt)

```
# Video Studio dependencies (separate from main requirements.txt)
# Install with: pip install -r requirements_video.txt
playwright>=1.45.0
moviepy>=2.2.0
opencv-python>=4.8.0
Pillow>=10.0.0
manim>=0.20.1         # For concept animations — may require Conda on Windows
edge-tts>=6.1.9       # Already in requirements.txt
ffmpeg-python>=0.2.0  # For complex filter graphs
numpy>=1.24.0         # Already installed with opencv
```

---

## Zero-Setup Auto-Installer (video_studio/setup.py)

The user runs one script. Everything else happens automatically.

```bash
python video_studio/setup.py
```

That's it. On success the script prints:

```
✓ All Video Studio dependencies installed
✓ Playwright Chromium browser ready
✓ FFmpeg verified
✓ Manim ready (concept animations enabled)

Run:  python video_studio/generate_all_videos.py
```

### Full setup.py implementation

```python
"""
video_studio/setup.py
Zero-interaction installer for MCPT Video Studio.
Run once, then run generate_all_videos.py.
"""
import sys, os, subprocess, shutil, platform, json
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ─────────────────────────────────────────────────
# ANSI colour output (works on Windows 10+ terminal)
# ─────────────────────────────────────────────────
class C:
    GREEN  = '\033[92m'
    YELLOW = '\033[93m'
    RED    = '\033[91m'
    BOLD   = '\033[1m'
    END    = '\033[0m'

def ok(msg):   print(f"  {C.GREEN}✓{C.END}  {msg}")
def warn(msg): print(f"  {C.YELLOW}⚠{C.END}  {msg}")
def fail(msg): print(f"  {C.RED}✗{C.END}  {msg}")
def head(msg): print(f"\n{C.BOLD}{msg}{C.END}")

# ─────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────
def pip(*args):
    """Run pip install silently; return True on success."""
    cmd = [sys.executable, '-m', 'pip', 'install', '--quiet', *args]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def pip_check(package):
    """Return True if package can be imported."""
    result = subprocess.run(
        [sys.executable, '-c', f'import {package}'],
        capture_output=True
    )
    return result.returncode == 0

def run_quiet(*cmd):
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

# ─────────────────────────────────────────────────
# Step 1 — Core pip packages
# ─────────────────────────────────────────────────
def install_pip_packages():
    head("Step 1/5 — Installing pip packages")
    reqs = ROOT / 'video_studio' / 'requirements_video.txt'
    packages = [
        ('playwright',      'playwright'),
        ('moviepy',         'moviepy'),
        ('opencv-python',   'cv2'),
        ('Pillow',          'PIL'),
        ('edge-tts',        'edge_tts'),
        ('ffmpeg-python',   'ffmpeg'),
        ('numpy',           'numpy'),
    ]

    for pip_name, import_name in packages:
        if pip_check(import_name):
            ok(f"{pip_name} already installed")
        elif pip(pip_name):
            ok(f"{pip_name} installed")
        else:
            fail(f"Could not install {pip_name} — check your Python environment")
            sys.exit(1)

# ─────────────────────────────────────────────────
# Step 2 — Playwright Chromium browser binary
# ─────────────────────────────────────────────────
def install_playwright_browser():
    head("Step 2/5 — Installing Playwright Chromium browser")
    # Try the normal install command first
    result = subprocess.run(
        [sys.executable, '-m', 'playwright', 'install', 'chromium'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("Playwright Chromium browser installed")
    else:
        # Fallback: use the installed binary directly
        import shutil as sh
        pw_bin = sh.which('playwright')
        if pw_bin:
            result2 = subprocess.run([pw_bin, 'install', 'chromium'],
                                     capture_output=True, text=True)
            if result2.returncode == 0:
                ok("Playwright Chromium browser installed (via binary)")
                return
        fail("Could not install Playwright Chromium browser")
        print(f"     Error: {result.stderr.strip()[:200]}")
        print("     Try manually: playwright install chromium")
        sys.exit(1)

# ─────────────────────────────────────────────────
# Step 3 — FFmpeg
# ─────────────────────────────────────────────────
def verify_ffmpeg():
    head("Step 3/5 — Verifying FFmpeg")
    if shutil.which('ffmpeg'):
        ok("FFmpeg found in PATH")
        return

    # Windows: try to download a static build automatically
    if platform.system() == 'Windows':
        warn("FFmpeg not found — attempting automatic download for Windows")
        _download_ffmpeg_windows()
    else:
        fail("FFmpeg not found in PATH")
        print("     Mac:   brew install ffmpeg")
        print("     Linux: sudo apt install ffmpeg")
        print("     After installing, re-run this setup script.")
        sys.exit(1)

def _download_ffmpeg_windows():
    """Download ffmpeg static build for Windows and add to PATH for session."""
    import urllib.request, zipfile, stat

    ffmpeg_dir = ROOT / 'video_studio' / '_ffmpeg'
    ffmpeg_exe = ffmpeg_dir / 'ffmpeg.exe'

    if ffmpeg_exe.exists():
        ok("FFmpeg static build already downloaded")
        _add_to_path(ffmpeg_dir)
        return

    ffmpeg_dir.mkdir(parents=True, exist_ok=True)
    # Gyan.dev provides reliable FFmpeg Windows builds
    url = ('https://github.com/GyanD/codexffmpeg/releases/download/'
           '7.1/ffmpeg-7.1-essentials_build.zip')
    zip_path = ffmpeg_dir / 'ffmpeg.zip'

    print("     Downloading FFmpeg (~35 MB) ...", end='', flush=True)
    try:
        urllib.request.urlretrieve(url, zip_path)
        print(" done")
    except Exception as e:
        print()
        fail(f"Could not download FFmpeg: {e}")
        print("     Download manually from https://ffmpeg.org/download.html")
        print("     Place ffmpeg.exe in your PATH, then re-run setup.")
        sys.exit(1)

    print("     Extracting ...", end='', flush=True)
    with zipfile.ZipFile(zip_path, 'r') as z:
        for member in z.namelist():
            if member.endswith('ffmpeg.exe'):
                data = z.read(member)
                ffmpeg_exe.write_bytes(data)
                break
    zip_path.unlink()  # remove zip after extraction
    print(" done")
    _add_to_path(ffmpeg_dir)
    ok("FFmpeg static build installed to video_studio/_ffmpeg/")

    # Write a small .bat wrapper so future sessions find it
    bat = ROOT / 'video_studio' / '_ffmpeg' / 'ffmpeg_path.py'
    bat.write_text(
        f"import os\nos.environ['PATH'] = r'{ffmpeg_dir}' + os.pathsep + os.environ.get('PATH','')\n",
        encoding='utf-8'
    )

def _add_to_path(directory):
    """Add directory to PATH for the current process and child processes."""
    os.environ['PATH'] = str(directory) + os.pathsep + os.environ.get('PATH', '')

# ─────────────────────────────────────────────────
# Step 4 — Manim (concept animations)
# ─────────────────────────────────────────────────
def install_manim():
    head("Step 4/5 — Installing Manim (concept animations)")

    if pip_check('manim'):
        ok("Manim already installed")
        return

    # Attempt standard pip install
    print("     Trying pip install manim ...", end='', flush=True)
    if pip('manim'):
        print(" done")
        ok("Manim installed via pip")
        return
    print(" failed")

    # Windows: pycairo often fails without Visual C++ Build Tools
    # Try the pre-built wheel approach
    if platform.system() == 'Windows':
        warn("pip install failed (likely pycairo/cairo issue) — trying pre-built wheels")
        # cairocffi is a pure-Python alternative to pycairo for Manim
        if pip('cairocffi') and pip('manim', '--no-deps') and pip('manim'):
            ok("Manim installed via cairocffi fallback")
            return

        # Final fallback: mark as unavailable, use pre-rendered concept MP4s
        warn("Manim could not be installed on this system")
        warn("Concept animations will use pre-rendered MP4s from the repo")
        warn("(All demo videos will still generate — only concept animations affected)")
        _write_manim_status(available=False)
    else:
        fail("Manim installation failed — check error above")
        print("     Mac/Linux: pip install manim")
        print("     This should work. Check Python version (3.8–3.12 required).")
        _write_manim_status(available=False)

def _write_manim_status(available):
    """Write manim availability to config so generate_all_videos.py can check."""
    status_file = ROOT / 'video_studio' / '.manim_available'
    status_file.write_text('yes' if available else 'no', encoding='utf-8')

# ─────────────────────────────────────────────────
# Step 5 — Verify MCPT app is runnable
# ─────────────────────────────────────────────────
def verify_mcpt():
    head("Step 5/5 — Verifying MCPT app")
    app_py = ROOT / 'app.py'
    if not app_py.exists():
        fail("app.py not found — run setup from inside the MCPT directory")
        sys.exit(1)

    start_bat = ROOT / 'Start_MCPT.bat'
    if start_bat.exists():
        ok("Start_MCPT.bat found")
    else:
        warn("Start_MCPT.bat not found — generate_all_videos.py will start app via Python directly")

    # Verify Flask and Waitress are importable
    for pkg in ['flask', 'waitress']:
        if pip_check(pkg):
            ok(f"{pkg} importable")
        else:
            fail(f"{pkg} not found — run: pip install -r requirements.txt")
            sys.exit(1)

# ─────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────
def print_summary():
    manim_file = ROOT / 'video_studio' / '.manim_available'
    manim_ok = manim_file.read_text().strip() == 'yes' if manim_file.exists() else True

    print(f"\n{'═'*52}")
    print(f"  {C.BOLD}{C.GREEN}Video Studio setup complete{C.END}")
    print(f"{'═'*52}")
    print(f"  ✓ All core dependencies installed")
    print(f"  ✓ Playwright Chromium browser ready")
    print(f"  ✓ FFmpeg verified")
    if manim_ok:
        print(f"  ✓ Manim ready (concept animations enabled)")
    else:
        print(f"  ⚠ Manim unavailable (pre-rendered concept MP4s will be used)")
    print(f"\n  Next step:")
    print(f"  {C.BOLD}python video_studio/generate_all_videos.py{C.END}")
    print(f"\n  The script will:")
    print(f"  1. Start MCPT on port 5060")
    print(f"  2. Seed it with demo data")
    print(f"  3. Generate all {51} videos ({C.BOLD}~2–3 hrs, fully automated{C.END})")
    print(f"  4. Launch review server at localhost:7777")
    print(f"  5. You review and approve — that's your only job")
    print()

if __name__ == '__main__':
    # Enable ANSI on Windows
    if platform.system() == 'Windows':
        os.system('color')

    print(f"\n{C.BOLD}MCPT Video Studio — Auto Setup{C.END}")
    print("This script installs all dependencies. No interaction required.\n")

    install_pip_packages()
    install_playwright_browser()
    verify_ffmpeg()
    install_manim()
    verify_mcpt()
    print_summary()
```

---

## generate_all_videos.py — FFmpeg Path Bootstrap

Add this block at the very top of `generate_all_videos.py` (before any other imports)
so the auto-downloaded FFmpeg binary is always in PATH:

```python
# Bootstrap: add auto-downloaded FFmpeg to PATH if present
import os
from pathlib import Path
_ffmpeg_path_script = Path(__file__).parent / '_ffmpeg' / 'ffmpeg_path.py'
if _ffmpeg_path_script.exists():
    exec(_ffmpeg_path_script.read_text(encoding='utf-8'))
```
