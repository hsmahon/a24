# Observed JSON schemas

JSON Schema draft 2020-12. Relative `$ref` values refer to sibling schema files. API schemas allow extra fields because these are inferred payloads from a deployed website, not an official versioned API specification.

| Schema | Payload / local file |
|---|---|
| `catalog-page.schema.json` | One film or TV catalog response with pagination |
| `title.schema.json` | One catalog title |
| `titles.schema.json` | `data/titles.json` |
| `image.schema.json` | A24 image metadata, including its origin URL |
| `video-metadata.schema.json` | A24 provider IDs and declared duration in seconds |
| `associated-content.schema.json` | An associated-content array |
| `videos.schema.json` | `data/videos.json`, normalized and deduplicated |
| `assets.schema.json` | `data/assets.json`, known image URLs and referencing titles |
| `brightcove-playback.schema.json` | Brightcove source metadata; duration is milliseconds |
| `playback-token.schema.json` | Request and response shapes; `$defs/request` and `$defs/response` |
| `download-status.schema.json` | `data/download-status.json`, keyed by local video ID |

`is_member_content` is an upstream catalog label, not a playback-access guarantee. A successful token or source response does not constitute a successful download. Download status uses `complete` only after a finished file passes ffprobe validation.
