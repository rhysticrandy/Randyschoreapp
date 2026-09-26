GUARDIAN RESET — WEEKLY EVENTS BUILD

This version adds a weekly-refreshing Explore event feed.

WHAT IT DOES
- The app loads events from events.json instead of relying only on hardcoded events.
- Explore's “This Week” filter always uses the phone's current date.
- A GitHub Action runs every Monday at 13:00 UTC and refreshes events.json from the Visit Colorado Springs free-events calendar.
- The updater geocodes event addresses with OpenStreetMap Nominatim and respects a 1.1-second delay between geocoding requests.
- You can also run the workflow manually from GitHub Actions.

SETUP
1. Upload the contents of this folder to the root of your GitHub Pages repository.
2. In GitHub, open Settings > Actions > General and make sure Actions are allowed.
3. The workflow needs permission to write repository contents; the workflow file requests that permission.
4. The first scheduled run will replace the starter events with newly fetched listings.

NOTE
The feed currently uses Visit Colorado Springs as its primary source. The site may change its HTML/structured data over time, so if the updater stops finding events, the fallback events bundled in index.html keep the Explore tab usable until the parser is adjusted.
