# Pillulu Health Assistant - Frontend

Vanilla HTML/CSS/JS frontend for medication search, AI Q&A, pillbox management, profile, and notifications.

## Highlights

- Medication search with typeahead suggestions (up to 3)
- Search result cards with visual metadata (image/imprint/color/shape)
- Click-to-open medication detail modal, then add directly to pillbox
- Camera label scan (Tesseract.js OCR) to fill search input
- AI Q&A section with "add suggested meds" shortcuts
- Pillbox cards with reminder schedules and visual enrichment indicators
- Profile modal with age, gender, height, weight, and location
- Body Insight panel with body-map interactions and case history list
- AI response cards that can surface related history context
- Google OAuth entry in login modal

## Configuration

Edit `app.js` and set `API_BASE` to your backend URL:

```javascript
const API_BASE = "https://YOUR-RENDER-URL.onrender.com";
```

For local development (backend on port 8000), it auto-detects localhost automatically.

## Local Development

1. Serve the frontend (any static server):
   ```bash
   cd frontend
   python -m http.server 8080
   ```
2. Open http://localhost:8080
3. Ensure backend is running at http://127.0.0.1:8000

## UI Notes

- The Google login button style is tuned for high contrast and keyboard focus.
- Search suggestions are debounced and cached in the browser for faster typing feedback.
- Medication detail modal is shared between search and pillbox cards for consistent UX.

## GitHub Pages

1. Push `frontend/` to repo.
2. In repo Settings → Pages, set source to main branch, root or /frontend.
3. Update `API_BASE` in app.js to your Render backend URL.
4. If frontend is in `/frontend`, base URL is `https://USERNAME.github.io/REPO/frontend/`.

## Design

- Color palette: #bee9e8, #62b6cb, #1b4965, #cae9ff, #5fa8d3
- Elderly-friendly: large fonts (18px+), high contrast, clear buttons
- Responsive layout
