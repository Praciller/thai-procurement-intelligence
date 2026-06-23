# Official source review

Decision: **approved with restrictions** on 2026-06-22.

| Item | Review |
| --- | --- |
| Source organization | Digital Government Development Agency (Public Organization), with source-data cooperation from the Comptroller General's Department and other named public bodies |
| Source system | Thailand Government Data Catalog (`data.go.th`), dataset `egp-contact-2568` |
| Dataset URL | <https://data.go.th/dataset/3beb7813-3607-4e5f-a094-b3b574a6e358> |
| Download URL | <https://data.go.th/dataset/3beb7813-3607-4e5f-a094-b3b574a6e358/resource/35961821-d945-4fc0-8ce1-a96b4cd46bd6/download/2568-egp-contract-10.csv> |
| Access date | 2026-06-21; metadata rechecked through the portal API on 2026-06-22 |
| Format | CSV; upstream resource size 168,019,099 bytes |
| Visible license | `Creative Commons Attributions` as returned by the official catalog API; no version or license URL is supplied |
| Intended use | Reproducible portfolio analysis of a bounded, attributed public-data snapshot |
| Attribution | Name DGA/data.go.th, link the dataset, retain the stated license, access date, and snapshot checksum |
| Update frequency | Not stated; resource last modified 2026-05-11 |
| Coverage | Fiscal-year 2568 EGP contract data; this project uses only 250 unique projects from resource part 10 |
| Available fields | Project ID/name/type, agency, method, dates, budget/reference/agreed amounts, fiscal year, and province |
| Rate limits | Not stated for the downloadable resource. Acquisition makes one bounded range request with a timeout and size limit. |
| Raw redistribution | Permitted under the catalog's stated attribution license, with attribution and this bounded subset only |
| Derived redistribution | Permitted with the same attribution and provenance notice |
| Privacy | Supplier names, tax/legal identifiers, and fields after province are excluded as unnecessary |
| Known limitations | License version is unspecified; snapshot is small, non-random, from one resource part, and not representative of all Thai procurement |

Restrictions:

- Keep the exact attribution, source URL, retrieval timestamp, and checksum with the snapshot.
- Do not describe the subset as complete, current, representative, or real-time.
- Do not use the data to allege fraud, corruption, misconduct, or suspicious behavior.
- Re-review the catalog metadata before replacing or expanding the snapshot.

The official CKAN-compatible API response used for review was `GET https://data.go.th/api/3/action/package_show?id=3beb7813-3607-4e5f-a094-b3b574a6e358`.
