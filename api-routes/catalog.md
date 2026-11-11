# Catalog

- `GET https://api.a24films.com/api/web/v1/films/`
- `GET https://api.a24films.com/api/web/v1/television/`

No user authorization was supplied in the successful tests. Query `page=2` advances pagination. The site's JavaScript also uses `sort`; its full accepted vocabulary was not established. Follow the returned `next` URL until null.

```json
{
  "count": 145,
  "next": "https://api.a24films.com/api/web/v1/films/?page=2",
  "previous": null,
  "results": []
}
```

The example abbreviates `results`; real entries include `display_name`, `slug`, `title_type`, artwork, release information, directors, and cast. The captured pages contained 50 entries per full page. Retrieved totals: 145 films across three pages and 52 TV entries across two.

Schema: [`catalog-page.schema.json`](../schemas/catalog-page.schema.json). Evidence: `data/catalog/` and normalized `data/titles.json`. HTTP 429 occurred during the initial associated-content crawl; honor rate limits and retry rather than assuming empty results.
