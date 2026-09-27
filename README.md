# Where the water is, the map is not

Best Bias Discovery entry for the Zindi / Humane Intelligence **Bias Bounty Mapping Equity Challenge** (Zindi user Shivoo29).

This repository checks the 238 heat-relief sites of Maricopa County's 2026 Heat Relief Network (cooling centers, respite centers, hydration stations) against Overture Maps places (release 2026-08-19.0). Hydration stations are absent from the open map twice as often as cooling and respite centers: 28.8% against 14.2%, Fisher p = 0.008 (0.023 after Bonferroni ×3). No site can be identified on the map as a heat-relief site.

**Writeup:** [writeup/bias_discovery.md](writeup/bias_discovery.md)

## Files

| file | what it is |
|---|---|
| `heat_relief.py` | Matches each site to Overture places within 150 m by name. Writes the per-site table, the tract access table, and a blank audit sheet if none exists. |
| `audit_results.py` | Reads the hand-audited sheet and prints every table and test in the writeup (writeup section 2.3). |
| `extra/hrn_audit.csv` | The audit: one row per site, with the automatic match, the places within 150 m, an OpenStreetMap link, and the verdict and note. |
| `extra/hrn.geojson` | Snapshot of the MAG Heat Relief Network public layer, retrieved 2026-09-27T17:20:26Z, sha256 `a130c1f75b6798481c5b656af21132e1699939803d79ee30a3d9845a7c8837d9`. It is included because the layer is seasonal (May 1 – Sept 30) and the live service may change. |
| `extra/research_heat.md` | Sources for the impact section (heat-death reports, CDC MMWR, Overture schema), with quotes and URLs. |

## Reproduce

Tested with Python 3.13 on Linux, with the versions in `requirements.txt`. The code has no randomness.

```bash
pip install -r requirements.txt

# Challenge data: the three Maricopa files the scripts read (no credentials needed)
B=s3://us-west-2.opendata.source.coop/humane-intelligence/bias-bounty-mapping-equity-challenge
aws s3 cp --no-sign-request $B/reference/maricopa-az/maricopa-az-overture-pois.parquet data/reference/maricopa-az/
aws s3 cp --no-sign-request $B/strata/maricopa-az/maricopa-az-census-tracts.parquet data/strata/maricopa-az/
aws s3 cp --no-sign-request $B/strata/maricopa-az/maricopa-az-strata-tract-table.parquet data/strata/maricopa-az/

python heat_relief.py      # matching and access analysis (keeps the existing audit sheet)
python audit_results.py    # final tables and tests
```

To re-fetch the live layer instead of using the snapshot (the audit sheet's ids follow the snapshot's row order):

```bash
curl -s "https://services1.arcgis.com/MdyCMZnX1raZ7TS3/arcgis/rest/services/HRN_Public_view/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson" -o extra/hrn.geojson
```

## Data and licences

- **Challenge data:** CC BY-SA 4.0. Overture places are mostly CDLA Permissive 2.0.
- **MAG Heat Relief Network layer (additional source, Best Bias Discovery only):**
  - Public and queryable without login.
  - Its ArcGIS item (bd08dde5206543018fe41da60d2551a7) carries an accuracy disclaimer and no explicit licence.
  - The snapshot is included only for reproducibility and will be removed on request.
- **Code:** MIT.
