# Observed API routes

Observed 2026-11-10 against A24's deployed site and its referenced providers. These are website implementation endpoints, not a documented stable A24 developer API.

| Method | URL / pattern | Purpose | Detail |
|---|---|---|---|
| GET | `https://api.a24films.com/api/web/v1/films/` | Paginated film catalog | [catalog.md](catalog.md) |
| GET | `https://api.a24films.com/api/web/v1/television/` | Paginated TV catalog | [catalog.md](catalog.md) |
| GET | `https://api.a24films.com/api/web/v1/titles/{slug}/associated/` | Supplemental video metadata | [associated.md](associated.md) |
| POST | `https://api.a24films.com/api/web/v1/playback-token/` | Ordinary per-video playback authorization | [playback-token.md](playback-token.md) |
| GET | `https://players.brightcove.net/6276845754001/5VNlpCFza_default/index.min.js` | Public player configuration | [brightcove.md](brightcove.md) |
| GET | `https://edge.api.brightcove.com/playback/v1/accounts/6276845754001/videos/{id}` | Current video source metadata | [brightcove.md](brightcove.md) |
| GET | `https://api-asset-production.s3.amazonaws.com/media/images/{object}` | Known public image object | [s3.md](s3.md) |
| GET | `https://api-asset-production.s3.amazonaws.com/?list-type=2&max-keys=2` | Tested bucket listing | [s3.md](s3.md) |

Film/TV HTML routes (`/films/{slug}`, `/television/{slug}`) also embed structured React Server Component payloads. They are HTML pages, not JSON API routes. `GET /api/web/v1/titles/{slug}/` did not return usable JSON in the test and is not relied upon.
