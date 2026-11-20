# HimalayaIQ — Smart Nepal Trek Finder

A local Python/Streamlit application for exploring Nepal's trekking routes, comparing preference compatibility, saving favorites and planning approximate costs. Final development lives on `feature/final-development`; `main` retains Deliverable 2.

## Run on Windows

Use Python 3.13 (verified with 3.13.7). Open PowerShell in this repository:

```powershell
git switch feature/final-development
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the printed local URL, normally http://localhost:8501. No activation, execution-policy change, API key, account or deployment is needed. Use `requirements.txt` instead for application-only installation. Internet is required for dependency installation and live forecasts; catalog, images, favorites, comparisons and budget calculations work offline afterward. Stop the server with Ctrl+C.

## Features

- **Explore:** six sourced itineraries; preference questionnaire; ranked cards with factor-level explanations and independent experience warnings.
- **Favorites:** add, view and remove favorites, persisted in local SQLite across sessions.
- **Compare:** choose up to four routes; photographs, region, duration, costs, difficulty, experience, altitude and interests; CSV export.
- **Budget:** editable package price, daily extras, flights, visa, insurance, equipment, tips, extra nights, contingency and party size; category breakdown and CSV export.
- **Weather:** live three-day forecasts at verified settlement locations, clear location context, missing-value handling and errors that do not disable recommendations.
- **Route details:** cultural highlights, route considerations, seasons, sources and selected landmark elevation charts.
- **Local photographs:** six destination-specific Wikimedia Commons images with visible attribution, stored licenses and fallback behavior for missing/corrupt files.

Input values persist when switching screens within a session. Favorites persist across application restarts. Budget scenarios and preferences are session-only; export a budget CSV to keep its category amounts.

## Curated routes and provenance

| Profile | Days in Nepal | Editorial experience expectation | Primary source |
|---|---:|---|---|
| Langtang Valley | 10 | Intermediate | [Package](https://www.nepalhikingteam.com/package/langtang-valley-trek) |
| Mardi Himal | 9 | Intermediate | [Package](https://www.nepalhikingteam.com/package/mardi-himal-trek) |
| Annapurna Base Camp | 14 | Intermediate | [Package](https://www.nepalhikingteam.com/package/annapurna-base-camp-trek) |
| Ghorepani Poon Hill | 8 | Beginner | [Package](https://www.nepalhikingteam.com/package/annapurna-panorama-trek) |
| Everest Base Camp | 16 | Experienced | [Package](https://www.nepalhikingteam.com/package/everest-base-camp-trek) |
| Manaslu Circuit | 14 | Experienced | [Package](https://www.nepalhikingteam.com/package/manaslu-circuit-trek) |

`data/treks.json` stores URLs, review dates, group-price context, cultural highlights and altitude qualifications. Original profiles were reviewed November 19, additions November 20, 2026. These first-party sources establish the operator's specific products, not independent safety assessments or market-wide pricing. Difficulty labels follow the operator; experience expectations and interest tags are editorial. The original three profiles' classifications remain unchanged.

**Duration:** Kathmandu arrival through departure, including listed transfers and city stays, not walking days alone. International travel days and additional delays are extra. Everest's selected package includes its stated buffer day and scheduled Lukla flights. Fixed published durations have equal minimum/maximum fields; the app never invents shorter itineraries.

**Budget:** USD per person for the guided package, not the whole holiday. Ranges span advertised party-size tiers. The low price may require a larger group; the form does not infer a solo quote, availability or group discount.

General inclusions: listed shared accommodation, city breakfasts, trekking meals, listed airport/ground transfers, guide/porter services, package permits and administration/taxes. Route-specific notes override these general assumptions. Everest includes scheduled Lukla flights; some packages include tea/coffee and selected showers.

General extras: international flights, visa, traveler insurance, unlisted city meals, personal equipment, tips, snacks, water, unlisted drinks, showers, Wi-Fi/charging, upgrades, extra nights and delay/emergency expenses. Check exact inclusions with the provider. The budget estimator adds only user-entered extras to the package; default zeros mean **not estimated**, not free. Party total multiplies per-person assumptions without inferring discounts. Contingency applies to all entered categories. Money uses decimal rounding at category level.

**Elevations:** charts compare selected published landmark heights. They are not continuous elevation profiles, distance plots, day-by-day plans or acclimatization advice. Optional/alternative viewpoints are labeled. The source's conflicting optional Manaslu base-camp altitudes are not plotted. Langtang's Kyanjin altitude discrepancy and ABC's December-season discrepancy are disclosed in route notes/sources.

## Photographs and Nepal identity

Mountain blue, forest teal and a restrained crimson accent frame destination photography and accurately labeled regional context. English is primary; no unsupported translations or decorative cultural claims are generated.

Images are stored in `assets/treks/`. [Image credits](assets/image-credits.json) record creators, Commons pages, download URLs, licenses, review dates, captions and display cropping. Preserve those credits when redistributing. [Asset notes](assets/README.md) explain per-photo licenses. Photos of optional or higher variants are explicitly captioned; Nepal-side Everest imagery was verified and Tibet-side search results excluded. Each card's image has descriptive alternative text. No external image URL is needed at runtime.

## Explainable scoring

`recommend()` validates preferences, filters out routes exceeding available days or minimum package budget, and ranks the remaining routes. No constraint is silently relaxed.

| Factor | Weight | Compatibility |
|---|---:|---|
| Duration | 25% | Full credit when the complete itinerary fits |
| Budget | 20% | 50% at minimum estimate, linearly increasing to 100% at maximum |
| Travel month | 15% | 100% in listed preferred months; 25% otherwise |
| Interests | 20% | Fraction of distinct selected interests matched |
| Experience | 20% | 100% at/above editorial expectation; 50% one level below; 0% two below |

`range_compatibility()` supports sourced duration/cost ranges: zero below minimum, 0.5–1 within, one at/above maximum. No interests removes that factor and normalizes the rest. Custom weights must be finite/nonnegative and leave an active positive factor; scaling prevents numeric overflow. Scores sort before rounding, then alphabetically for ties. More available time/budget never penalizes a route. Experience warnings are calculated independently and remain even with zero experience weight.

**Compatibility is preference fit, never trekking safety or medical fitness.** The weights are transparent design choices, not a trained or validated predictive model. Weather and budget-estimator outputs do not alter questionnaire inputs or ranking.

## SQLite and modules

The app initializes `data/himalayaiq.sqlite3` automatically; the data folder must be writable. JSON is the curated catalog's source of truth. Seed hashes trigger transactional refreshes of the `treks` cache. The additive `favorites(trek_id, saved_at)` table is independent and never cleared by catalog refresh. Unavailable saved route IDs remain visible for explicit removal. Favorites are shared by users of this local installation; there is no authentication or cloud synchronization. Back up the database file while the app is stopped to preserve favorites. Do not delete it to reset the catalog.

| Module | Responsibility |
|---|---|
| `app.py` | Entry point, navigation, theme and retained widget state |
| `himalayaiq/ui.py` | Reusable views and error presentation |
| `models.py` | Trek, preferences and recommendation dataclasses |
| `validation.py` | Preference, seed and elevation validation |
| `database.py` | Validated JSON loading and SQLite catalog synchronization |
| `recommender.py` | Modular filtering, scoring, warnings and explanations |
| `favorites.py` | Parameterized SQLite favorite operations |
| `budget.py` | Validated, decimal-based budget calculations |
| `catalog.py` | Comparison records and safe local image resolution |
| `weather.py` | HTTP client, timeouts and forecast parsing |
| `assumptions.py` | Shared cost/duration wording |

Dependencies: Streamlit, requests, pandas, Pillow; pytest for tests. Dataclasses, JSON, SQLite and decimal come from Python's standard library. No ML, chatbot, paid service or additional web framework.

## Weather integration

The [Open-Meteo API](https://open-meteo.com/en/docs) supplies daily low/high temperatures (°C) and precipitation (mm), timezone `Asia/Kathmandu`, for three upcoming days. Connect/read timeouts are 5/15 seconds. Validation covers dates, units, lengths, numeric values and missing fields; missing values are never replaced with zero. No synthetic production fallback exists.

Coordinates were verified through Open-Meteo/GeoNames: Dhunche in Rasuwa (Langtang), Pokhara (Annapurna routes), Namche Bazaar (Everest), and Kathmandu arrival city (Manaslu). These are settlement forecasts, not whole-route or summit conditions. Kathmandu is deliberately labeled only as the arrival city. The selected travel month does not request a long-range forecast. Changing routes hides the previous route's result. Refresh replaces old results, including with an error on failure. The cache lasts 15 minutes but explicit refresh bypasses it. Dates and UTC retrieval timestamps remain visible.

## Testing and troubleshooting

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/check_live_weather.py
.\.venv\Scripts\python.exe -m pip check
```

Pytest uses isolated databases for favorite/UI tests and synthetic weather fixtures only inside tests. Coverage includes original three-route regressions, six-route profiles, scoring boundaries, ties, monotonicity, large custom weights, validation, SQLite refresh/persistence, images, budgets, navigation and weather failures. The live script makes real requests for each unique location and exits nonzero on failure. Actual results and remaining limitations are recorded in [technical development status](docs/final-development-status.md).

Verified November 20, 2026: **76 tests passed** in a newly installed environment with system packages disabled; `pip check` passed; Streamlit launched and its health endpoint returned HTTP 200. Four real forecast-location checks passed. Desktop and 390-pixel mobile browser checks were also performed.

If weather fails, check internet access and retry; offline features still work. For database errors, check write permissions and close other processes holding locks. For a missing image, the app shows a route-specific placeholder. Reinstall dependencies if Streamlit cannot import. Use a different `--server.port` if the default port is occupied.

## Scope and remaining limitations

This is a reviewable local final-development build, not a booking service. Prices are approximate single-operator references; no live quotation or group-size pricing engine is included. Landmark charts are not GPS route profiles. Weather remains settlement-level. Budgets require user estimates. Full assistive-technology and real-device testing remains broader than the automated suite. Favorites are device-local.

Future improvements: independent route-source cross-checks, richer licensed photo choices, group-size-aware costing, more route-specific verified forecast points, and optional saved budget scenarios. No authentication, deployment, ML or itinerary generator is planned for this branch.

The [Deliverable 1 proposal](docs/deliverable-1-proposal.md), [Deliverable 2 status](docs/deliverable-2-status.md) and original diagrams are preserved unchanged. Academic presentation/submission materials are intentionally left to the project owner.
