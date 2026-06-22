# Official source mapping

Mapping version: `dga-egp-v1`.

| Official field | Canonical field | Transformation | Required | Validation | Notes |
| --- | --- | --- | --- | --- | --- |
| `รหัสโครงการ` | `source_record_id` | Trim whitespace | Yes | Non-blank; unique within snapshot | Stable source key |
| `ชื่อโครงการ` | `project_name` | Trim and collapse whitespace | Yes | Non-blank; bounded by database field | No generated replacement |
| `ชื่อหน่วยงาน` | `agency_name` | Trim and collapse whitespace | Yes | Non-blank | Source spelling retained |
| `จังหวัด` | `province` | Trim; known aliases normalized | No | String or null | Unknown remains null |
| `กลุ่มวิธีจัดซื้อฯ`, `วิธีจัดซื้อฯ` | `procurement_method` | Prefer group, then method | No | String or null | No category inference |
| `ชื่อประเภทโครงการ` | `procurement_category` | Trim whitespace | No | String or null | Source value retained |
| `งบประมาณ(บาท)` | `budget_amount` | Remove grouping characters; decimal THB | No | Finite and non-negative | Currency is THB |
| `ราคาตกลงซื้อ/จ้าง` | `winning_amount` | Remove grouping characters; decimal THB | No | Finite and non-negative | Null when absent |
| `วันที่ประกาศ`, `วันที่เกิดรายการ` | `announcement_date` | Prefer announcement; fall back to event date; convert Buddhist Era to Gregorian | No | Valid calendar date | Thai abbreviated months supported |
| Snapshot metadata | provenance fields | Copy immutable metadata | Yes | Official HTTPS domain; checksum match | Includes snapshot, retrieval, license, mapping version |

Missing optional values remain null. A row is rejected when a required canonical or provenance field is absent, an amount is negative or invalid, a date cannot be parsed, or the source URL is outside the approved official domain. Duplicate identity is `(source_name, source_record_id)`; reruns update changed rows and count unchanged rows without inserting duplicates.

Text is whitespace-normalized only. Organization names are not merged heuristically. Mapping versions change only when source-field semantics or transformations change; metadata-only documentation changes do not require a new version.
