# Download failure triage — 2026-11-11

The original 12 failures were checked against fresh public-policy and, for the protected entries, A24-authorized Brightcove playback responses. Tokens and keys are omitted from this report.

## Duration mismatches

Six staged files match the current Brightcove asset durations. Their website catalog durations were stale. Recovery requires video/audio stream checks, duration agreement with Brightcove, and a full FFmpeg decode with error termination enabled before moving the files into the media directory.

| Video | ID | Site seconds | Brightcove seconds | Current result |
|---|---|---:|---:|---|
| Deleted Scenes | `6330701671112` | 65 | 164.992 | complete |
| Dicks: The Musical Trailer | `6332311263112` | 60 | 117.099 | complete |
| Heretic: Trailer | `6355612291112` | 123 | 143.296 | complete |
| A Different Man: Trailer | `6358088736112` | 109 | 99.925 | complete |
| Bring Her Back: Trailer | `6370874544112` | 109 | 99.093 | complete |
| Eternity: Trailer 2 | `6382737352112` | 187 | 86.741 | complete |

## DRM-only sources

For each entry below, all eight returned sources are DRM protected. Both the public player-policy API and the authorized `edge-auth.api.brightcove.com` API returned FairPlay HLS and Widevine/PlayReady DASH sources, with no unprotected downloadable source. The old `skd` error was a DRM detection failure in this downloader; it is now reported explicitly.

| Video | ID |
|---|---|
| Midsommar: Director's Cut | `6333140736112` |
| Never Goin' Back: Trailer | `6335394242112` |
| Past Lives: Trailer | `6337958501112` |
| Porous Walker x Dicks: The Musical Lyric Video | `6342802072112` |
| Deleted Scenes | `6354523723112` |
| The Making of Mother Mary | `6399137982112` |

No playable portable MP4 has been downloaded for these six entries. Finishing them requires owner/provider-supplied downloadable renditions, source exports, or account access that permits those exports. Downloading encrypted segments alone would not produce the requested playable video files.

Provider field definitions: [Brightcove video fields](https://apis.support.brightcove.com/playback/references/playback-api-video-fields-reference.html). [Brightcove DRM overview](https://support.brightcove.com/shared/s-general/overview-digital-rights-management-drm-video-cloud.html) explains how DRM affects available renditions. Raw observed responses are retained locally under `data/triage/` and excluded from this public repository; their signed URLs are temporary.

## Downloader corrections

- Validate against current provider duration instead of stale catalog duration.
- Recover and fully decode an existing staged file when it matches the provider asset.
- Select only sources without `key_systems`; explicitly reject DRM-only source sets.
- Add `--failed-only` to retry failures without disturbing successful entries.
- Keep status, keys, logs, and temporary media in the project; finished files remain directly under `<media-output>/`.

No source exports or provider-owner access were available during this investigation. These six remain blocked.
