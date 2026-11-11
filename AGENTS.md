# A24 workspace instructions

- Keep all source code, documentation, API descriptions, schemas, raw responses, manifests, keys, logs, download status, and temporary files in `<project>/`.
- `<media-output>/` must contain only verified, finished Brightcove video files directly at its root. Do not create subdirectories, download images or YouTube videos, or put scripts, logs, metadata, hidden staging directories, partial downloads, or status files there. The user explicitly removed images and all 18 YouTube references from the download scope.
- Stage downloads in `data/staging/` in this project. Verify a finished video with ffprobe before moving it into the media directory.
- Keep all Python scripts in `scripts/`; resolve project data relative to the checkout root.
- Keep API documentation in `api-routes/` and JSON Schema documents in `schemas/`. Explain the delivery architecture and observed limitations in `README.md`.
- The user authorized downloading media from A24 and the services it uses. Use the site's ordinary public catalog and playback flow; record HTTP failures and missing content rather than claiming complete storage access.
- Refresh expiring source URLs and obtain playback tokens through A24's normal endpoint. Keep tokens and keys out of documentation and console logs.
- Respect rate limits. Distinguish catalog entries, downloadable references, successfully downloaded files, full features, and TV episodes. Never describe a manifest or token response as a completed download.
- Do not commit, push, publish, or send messages to third parties unless requested.
