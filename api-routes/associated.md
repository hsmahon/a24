# Associated content

`GET https://api.a24films.com/api/web/v1/titles/{slug}/associated/`

Successful unauthenticated requests returned an array of supplemental content objects. Important fields:

| Field | Meaning |
|---|---|
| `slug` | Input to the playback-token request |
| `name`, `display_name` | Content labels |
| `content_type` | Trailer, featurette, deleted scenes, etc. |
| `is_member_content` | Upstream label; do not infer actual playback success from it |
| `static_art.src` | Referenced artwork object |
| `video.brightcove_id` | Brightcove Playback API video ID |
| `video.youtube_id` | Alternate provider reference |
| `video.duration_in_seconds` | Declared duration, seconds |

Schema: [`associated-content.schema.json`](../schemas/associated-content.schema.json). Evidence: `data/associated/`. Title-page embedded data also supplies `primary_trailer` and content objects; `harvest.py` merges and deduplicates references by provider/video ID. Supplemental content is not synonymous with the title's full film or TV episodes.
