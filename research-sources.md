# A24 public-source delivery research

Checked 2026-11-10. Findings combine first-party web research with the parent task's live HTTP inspection. Counts describe the currently exposed site catalog, not A24's entire historical library or storage account. Video retrieval is tracked in data/download-status.json; this research note does not claim the queue is complete.

## Public APIs and inventory

The site uses publicly readable JSON endpoints:

- `GET https://api.a24films.com/api/web/v1/films/` — paginated film catalog, 145 titles retrieved.
- `GET https://api.a24films.com/api/web/v1/television/` — paginated television catalog, 52 titles retrieved.
- `GET https://api.a24films.com/api/web/v1/titles/{slug}/associated/` — associated content, including videos.

Detail-page HTML also carries React Server Component data. These are observed site endpoints; no published bulk-export contract was identified.

Saved inventories: [titles.json](data/titles.json) contains 197 titles, [discovered-videos.json](data/discovered-videos.json) preserves the 351 originally discovered video entries, and [assets.json](data/assets.json) contains 701 artwork URLs. Of the video entries, 333 have Brightcove delivery and 18 are YouTube-only. The current active inventory in [videos.json](data/videos.json) includes only the 333 Brightcove entries; all images and YouTube media were deleted and excluded from downloads at the user's request. [inventory-errors.json](data/inventory-errors.json) is empty after retries. These counts do not imply that every media download has succeeded.

## Storage and video delivery

**S3 artwork origin:** `api-asset-production.s3.amazonaws.com`. This hostname occurs directly in API image URLs and in the first-party [Moonlight page's optimized image link](https://a24films.com/_next/image?q=75&url=https%3A%2F%2Fapi-asset-production.s3.amazonaws.com%2Fmedia%2Fimages%2FMoonlight_Thumb_UPDATED.jpg&w=3840). A live public bucket-list request returned XML `AccessDenied`; see [s3-list-response.xml](data/s3-list-response.xml). Known artwork URLs remain retrievable. The 701 artwork downloads totaled approximately 1.25 GB before their requested deletion. Public object reads do not establish a public bucket listing or access to unlisted objects.

**Brightcove:** account `6276845754001`, player `5VNlpCFza`. The site's official player JavaScript exposes its public player policy key; the long key is omitted here. The Playback API returns HLS and DASH source URLs. Observed media hosts include signed URLs on `manifest.prod.boltdns.net` and `fastly-signed-us-east-1-prod.brightcovecdn.com`. Evidence is saved under [playback](data/playback/) and [hls](data/staging/hls/), with the inspected player in [player.js](data/player.js).

**Normal playback token flow:** `POST https://api.a24films.com/api/web/v1/playback-token/` with JSON field `supplemental_video_content_slug` returned a JWT with an approximately 60-second lifetime. An encrypted HLS key request without a token returned HTTP 401; providing the issued token in the `BCOV-Auth` header successfully returned a 16-byte AES key. This demonstrates the ordinary playback authorization flow for tested content, not universal access to every title. Signed URLs and tokens are temporary.

## Full films versus promotional content

Most discovered videos are trailers, clips, interviews, and other supplemental material. [Moonlight](https://a24films.com/films/moonlight), for example, labels short promotional videos while its full-film action links to `app.a24films.com`. [The Curse](https://a24films.com/television/the-curse) exposes a trailer and identifies SHOWTIME as its premiere outlet.

One material exception is present in catalog extras: **Midsommar: Director's Cut**, Brightcove ID `6333140736112`, duration 10,213 seconds (approximately 2 h 50 m). Its playback-token request returned HTTP 200. This establishes a full-length catalog entry and a successful token response, not a verified completed feature download.

[A24's Terms of Use, section 10](https://a24films.com/terms-of-use) describes its separate VOD platform's subscription, rental, purchased, and free promotional content; section 10.E describes optional temporary offline viewing on supported devices. No complete film-library export or complete TV-episode collection has been established. No evidence shows that the artwork S3 bucket contains full film/TV masters.

## Scope of conclusions

The [film](https://a24films.com/films) and [TV](https://a24films.com/television) catalogs, their public APIs, associated videos, and known artwork objects are enumerable through the inspected site paths. The S3 bucket itself is not publicly listable in the tested request. Brightcove provides source manifests through its player/API and uses short-lived playback authorization for encrypted media. Complete storage enumeration, universal feature-film availability, episode availability, and completed video downloads are not claimed.
