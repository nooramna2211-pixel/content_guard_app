# Content Guard browser extension

Manifest V3 extension for Chromium-based browsers (Chrome and Edge). It checks
only Google Search and YouTube search-result queries against the local
Content Guard keyword list, forces Google SafeSearch for Google searches, and
shows a safety warning when a query matches a keyword. Normal Google,
YouTube, and Gemini pages remain accessible.

## Install for local testing

1. Start the Flask app on `http://127.0.0.1:5000`.
2. Open `chrome://extensions` or `edge://extensions` and enable **Developer
   mode**.
3. Choose **Load unpacked** and select this `extension` directory.
4. Add or remove terms in the Content Guard keyword settings.

The extension uses JSON `POST /api/check-keywords` requests to check only the
submitted or displayed search text. If the local API is unavailable, it leaves
search navigation alone. It does not check full page URLs or non-search page
content.

## Scope

- Google Search `/search?q=...` pages and Google search form submissions are
  checked against the keyword dictionary. Google `safe=active` is enforced on
  search URLs and search forms.
- YouTube `/results?search_query=...` pages and search form submissions are
  checked against the keyword dictionary. Home, watch, channel, and other
  YouTube pages are not keyword-checked.
- Gemini and other Google services are not intercepted.
- Custom blocked-domain redirects remain available for other domains, up to
  5,000 entries. Google and YouTube domains are excluded from dynamic block
  rules so they remain available.
- HTTP navigations for Google and YouTube are upgraded to HTTPS.

The extension does not inspect result-page contents, native application
traffic, or unrelated websites. Its decisions depend on the local Flask app
and the current keyword database.
