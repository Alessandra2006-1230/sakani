# Sakani Logo Asset

## Expected location
- Filename: `sakani_logo.png`
- Path: `assets/images/sakani_logo.png` (relative to project root)

## Specifications
- Dimensions: 512 × 512 px (square) recommended. The sidebar displays at ~46×46 px and will downscale automatically.
- Format: PNG preferred (transparency supported). The current loader uses Tkinter `PhotoImage(file=...)` which supports GIF and PPM/PGM natively; PNG support depends on Tk/Tkinter build. Use PNG when possible.
- Aspect ratio: Square recommended for best results in the circular/avatar-style sidebar container.
- Background: Transparent or solid is fine; the container provides its own background.

## Behavior
- If `assets/images/sakani_logo.png` exists and loads successfully, the sidebar will display it (subsampled if larger than the display size).
- If the file is missing or fails to load, the app falls back to a drawn vector leaf placeholder (no external assets required).
- The logo is displayed at approximately 44–56 px in the sidebar header.

## Notes
- Do not commit large binary assets unnecessarily. This directory is tracked via this README.
- The application does not currently require additional image dependencies beyond Tkinter's built-in image support.
