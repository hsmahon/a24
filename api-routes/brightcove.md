# Brightcove delivery

Observed account: `6276845754001`; player: `5VNlpCFza`; embed: `default`.

The public [player JavaScript](https://players.brightcove.net/6276845754001/5VNlpCFza_default/index.min.js) contains a player policy key. Obtain current configuration instead of treating the captured key as permanent.

```http
GET /playback/v1/accounts/6276845754001/videos/6330628367112 HTTP/1.1
Host: edge.api.brightcove.com
Accept: application/json;pk=<public player policy key>
```

The successful response includes `id`, `name`, `duration` (milliseconds), `sources`, artwork URLs, and text-track metadata. The inspected responses exposed HLS and DASH sources, rather than progressive MP4 source URLs. Schema: [`brightcove-playback.schema.json`](../schemas/brightcove-playback.schema.json); evidence: `data/playback/`.

Observed URL families:

- `manifest.prod.boltdns.net/manifest/...` — signed rendition manifests.
- `manifest.prod.boltdns.net/license/v1/aes128/...` — tested HLS key delivery.
- `fastly-signed-us-east-1-prod.brightcovecdn.com/media/...` — signed media segments.

These describe CDN delivery, not the location or accessibility of original master files. HLS master playlists select video renditions and audio groups. Variant playlists list segments and AES-128 key information. DASH sources were observed but the current downloader uses HLS. Fetching a manifest alone does not establish a playable completed file.

Source URLs carry expiring signing parameters. Refresh them via the Playback API. The [official API overview](https://apis.support.brightcove.com/playback/getting-started/overview-playback-api.html) describes policy keys/JWTs and cautions against hard-coding media URLs. Playback metadata does not itself authorize the encryption key request; see [playback-token.md](playback-token.md).

## DRM-only entries found during failure triage

Six entries returned only sources with `key_systems` populated, both from the public player-policy endpoint and from `edge-auth.api.brightcove.com` using the ordinary A24-issued per-video JWT. Their HLS sources specify FairPlay; their DASH sources specify Widevine and PlayReady. A `skd://` URI is a FairPlay identifier, not an HTTP AES-key download URL. The downloader now rejects protected sources explicitly instead of attempting to fetch `skd://` using urllib.

Brightcove documents [`key_systems` as a content-protection indicator](https://apis.support.brightcove.com/playback/references/playback-api-video-fields-reference.html). Its [DRM overview](https://support.brightcove.com/shared/s-general/overview-digital-rights-management-drm-video-cloud.html) explains that MP4 renditions are hidden from playback delivery when DRM is enabled. No non-DRM alternate was returned in these checks. Source exports or downloadable renditions must be supplied through the content owner/provider to complete portable video downloads for those six entries.

Full evidence and the duration discrepancy table are in [reports/failure-triage.md](../reports/failure-triage.md). Captured provider JSON is retained locally under `data/triage/` and excluded from the public repository because it contains temporary signed source/license URLs.
