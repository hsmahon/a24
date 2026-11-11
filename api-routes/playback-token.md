# Playback authorization

`POST https://api.a24films.com/api/web/v1/playback-token/`

Content-Type: `application/json`

```json
{"supplemental_video_content_slug": "moonlight-trailer"}
```

Observed successful response:

```json
{"jwt": "<short-lived A24-issued token>"}
```

Decoded test claims included `accid`, `iat`, `exp`, `conid`, and `vids`; `exp - iat` was 60 seconds. The downloader obtains tokens using the normal A24 route and uses them promptly. A token for one video must not be treated as a universal account token. Responses may deny playback; record that outcome.

For the tested HLS key URL, unauthenticated retrieval returned HTTP 401 and `bcov-jwt-validity: fail`. Sending the issued token in the `BCOV-Auth` header returned 16 bytes. Brightcove's [documented player flow](https://player.support.brightcove.com/playback/playback-restrictions-with-bcp.html) also describes propagating `bcov-auth` through the HLS master URL. This project's successful header test is an observation, not a guarantee for every provider path.

Schemas: [`playback-token.schema.json`](../schemas/playback-token.schema.json). Never copy active token values or encryption keys into documentation or console output.
