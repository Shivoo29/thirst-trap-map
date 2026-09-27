# Best Bias Discovery: where the water is, the map is not

**Maricopa's heat-relief hydration stations are missing from Overture twice as often as its cooling centers, and no heat-relief site can be identified as one**

Zindi user: Shivoo29. Scored submission: fJzXLpZM (challenge data only). This entry is for Best Bias Discovery. It uses one additional public dataset, documented in section 5.

## Summary

Heat kills hundreds of people a year in Maricopa County, which is at the centre of this study region. The county recorded 645 heat-related deaths in 2023, 608 in 2024 and 430 in 2025. About three quarters died outdoors, and people experiencing homelessness were the largest group each year (45%, 49%, 49%). The county's response is the Heat Relief Network (HRN): indoor cooling centers, respite centers, and hydration stations where people who are outside can get water. I checked all 238 HRN heat-relief sites in the network's public layer against Overture places (release 2026-08-19.0) and audited every non-identical match by hand.

- **Hydration stations are the least mapped.** 28.8% of them (38 of 132) are absent from Overture, against 14.2% (15 of 106) of cooling and respite centers. That is twice the rate (Fisher exact p = 0.008; 0.023 after correcting for the three comparisons I tested). Hydration stations are the part of the network built for people who are outdoors, the group that makes up three quarters of heat deaths.
- **The gap is deepest where vulnerability is highest.** In census tracts in the top quartile of CDC SVI, 16 of 41 hydration stations (39%) are absent. The rate is 22 of 91 (24%) elsewhere. This is suggestive, not significant after correction.
- **No heat-relief site can be identified as one.** Overture's places taxonomy has no cooling-center, heat-relief or hydration category, and the place schema has no opening-hours field. Even the 63% of sites that the map does carry under their own name cannot say that they offer heat relief, or when.

The automated scorecard reports the opposite: its summer-heat stratum shows heat-exposed tracts with coverage gaps 41% *smaller* than other tracts (ratio 0.59). Its facility terms (fire stations, EMS stations, schools and business establishments) do not include any facility that responds to heat.

## 1. The pattern, and why the scorecard does not surface it

1. **A stratum the scorecard does not have: the facility that answers the hazard.** The scorecard measures facilities that answer fires and medical calls, plus schools and businesses. Heat has its own response network, and nothing on the scorecard measures it.
2. **The heat stratum points the wrong way.** The hottest tracts are mostly urban, and urban tracts are well mapped overall, so the aggregate reads 0.59. Inside the heat-response layer, the sites that serve people who are outdoors are the ones missing.
3. **An attribute no count can see.** The scorecard compares counts and lengths. A place can be present and still carry no sign that it offers water or cooling, or when it is open.
4. **A pattern by service type, not by tract.** The disparity is between two kinds of heat-relief site within the same tracts and cities. The tract-level strata (SVI, CVI, urban/rural, tribal, hazard) cannot express it.

## 2. Evidence

### 2.1 Data
- **Official sites:** MAG Heat Relief Network public layer (section 5): 250 records, 238 with `HeatRelief = Yes`. These are 93 cooling centers, 13 respite centers and 132 hydration stations. Of them, 237 are in Maricopa County (04013) and 1 in Pinal (04021). MAG describes the network publicly as "more than 200 locations". The 238 is the count in its layer on 2026-09-27.
- **Map:** `maricopa-az-overture-pois.parquet` (challenge bucket, Overture 2026-08-19.0).
- **Strata:** `maricopa-az-census-tracts.parquet` and `maricopa-az-strata-tract-table.parquet` (challenge bucket), for tract GEOID and `svi_overall`.

### 2.2 Method
1. **Candidates:** every Overture place within 150 m of each site (NAD83 / UTM 12N).
2. **Automatic match on names, as token sets.** Punctuation, plural "s", stop words and the site's city name are removed. A pair matches at token Jaccard ≥ 0.6, or when one name's tokens are contained in the other's and include a non-generic word. The script asserts the false matches found in development, for example "Peoria Main Library" vs "Peoria Human Resources".
3. **Hand audit (`extra/hrn_audit.csv`).**
   - The 89 sites whose Overture name is identical after normalization are accepted automatically.
   - The other 149 were each judged from the list of places within 150 m, with the reason recorded.
   - Seven first-pass verdicts were overruled. The rulings are listed in `audit_results.py`.
   - Four borderline sites were settled the same way as similar rows in the sheet: ids 92, 93 and 113 are generic_name, and id 73 is absent.
4. **Final classes:**
   - **by_name:** the site's own name finds it.
   - **generic_name:** only an operator, library-system, former or host name is on the map, e.g. "Scottsdale Public Library" for its Mustang, Arabian and Civic Center branches.
   - **absent:** none of the places within 150 m is this facility.

The audit changed the picture. Before it, the automatic matcher suggested that sites run by nonprofits appear only under their operator's name far more often than government sites (p = 5×10⁻⁸). Once the library branches that appear under their system name were counted, the difference was 19.3% against 10.9% (p = 0.10), and I do not claim it.

### 2.3 Results (all 238 sites)

| type | sites | by_name | generic_name | absent |
|---|---|---|---|---|
| Hydration station | 132 | 57.6% | 13.6% | **28.8%** |
| Cooling center | 93 | 67.7% | 18.3% | 14.0% |
| Respite center | 13 | 76.9% | 7.7% | 15.4% |
| All | 238 | 62.6% | 15.1% | 22.3% |

The three comparisons I tested, as Fisher exact tests (× 3 for Bonferroni):

| comparison | rates | p | × 3 |
|---|---|---|---|
| absent: hydration vs cooling + respite | 28.8% vs 14.2% | 0.008 | **0.023** |
| absent: SVI top quartile vs rest | 31.7% vs 19.1% | 0.050 | 0.15 |
| generic_name: nonprofit vs government | 19.3% vs 10.9% | 0.10 | 0.31 |

**Sensitivity.** Seven sites matched only a neighbouring park, pool or studio, and I count them as absent. Six of them are hydration stations at recreation or community centers. If instead the park is taken to lead a user to the center, and those seven count as generic_name, the hydration gap is 24.2% vs 13.2% (p = 0.033; 0.10 after correction, so no longer significant). The direction holds, but the result's significance rests on whether a mapped park counts as a mapped recreation center. I think it does not: the refuge is the building, and the map gives no sign that the park has one.

**Where the missing hydration stations are.**
- **City of Phoenix recreation centers:** Harmon, Hayden, Verde Park, University Park, Eastlake Park, Holiday Park and Pecos. In each, the park, pool or library next door is on the map, and the building with the water and air conditioning is not.
- **Tract 04013114900** (SVI 0.99, south-central Phoenix) has three absent sites: Harmon Recreation Center, Marcos de Niza Senior Center, and Apex Transitional Housing's Memorial Hospital site.
- **Recovery and behavioral-health sites:** Unhooked Recovery, Sanctuary Recovery Centers, Copa Health Metro Center, and Terros Health's 27th Avenue, 51st Avenue and 23rd Avenue centers.
- **Faith and community sites:** ATR Resource Services, 1111 W. Hatcher (Cleo N Lewis Ministries), St. Joseph the Worker (Mesa), DREAMreach Ministry, and Native American Connections' Devine Legacy.

**Even when present, the function is missing.** The 149 sites found by name are spread over 29 Overture categories. About half (78) are in a category a person would search for refuge: library, community center, senior center, recreation venue or homeless shelter. The rest are filed under clinics, churches, government offices, and in one case `french_restaurant` (St. Vincent de Paul's Mesa Dining Room). No category and no attribute marks any of them as heat relief.

### 2.4 What I tested and did not find
- **No operator-type disparity after audit.** Nonprofit vs government, generic_name: p = 0.10 (see above).
- **No access disparity by SVI.** For 1,009 Maricopa tracts, I computed the population-weighted extra distance from each tract's interior point to the nearest site found by name, compared with the nearest official site. The extra distance is smaller in the top SVI quartile (0.40 km) than in the bottom (0.68 km). This used the automatic statuses.
- **Not a confidence or status effect.** Overture `confidence` has a median of 0.99 for matched sites of both operator types. One matched place (Copa Health, Florian) carries `permanently_closed` although it is an active 2026 site.

## 3. Who is affected, and why it matters

Maricopa County Department of Public Health, Heat-Related Deaths Reports:

| year | deaths | experiencing homelessness | outdoors | substances involved |
|---|---|---|---|---|
| 2023 | 645 | 45% | 75% | 65% |
| 2024 | 608 | 49% | 77% | 57% |
| 2025 | 430 | 49% | 74% | 55% |

- **Not knowing where to go is the main barrier.** In the county's 2023 cooling-center survey (CDC MMWR 74(14), 2025), common barriers were "lack of awareness (36% visitors; 49% public), uncertainty of locations (17% visitors; 22% public), and transportation challenges for visitors (31%)". The county responded by funding a heat-relief call center "to facilitate location of and transportation to and from cooling centers".
- **Outside call-center hours, map data is the channel.** The public is directed to the HRN web map and to 211 Arizona, whose operators answer "from 9 a.m. to 7 p.m. daily". Outside those hours, and in any general-purpose map app, open map data decides what a search returns.
- **Outreach and dispatch.** Street-outreach teams handing out water, and dispatchers taking heat-illness calls, need to route people to the nearest open relief site. On open map data, the sites built for people who are outdoors are the ones most likely to be missing. None of the sites can be found by function, so "nearest cooling site" cannot be answered from the map at all.
- **The missing sites include the most vulnerable tracts.** Several of the missing recreation centers in south-central Phoenix sit in tracts at the top of the SVI distribution, such as 04013114900 (SVI 0.99). Across the whole network, the SVI pattern is suggestive, not significant (section 2.3).

## 4. What would close the gap
- Ingest the HRN layer as an Overture places source. It is public, geocoded and republished every season.
- Map recreation-center buildings as places, not only the parks around them.
- Add a heat-relief/cooling-center category (or attribute) and an opening-hours field to places.
- Keep branch names when conflating multi-site operators.

## 5. Reproducing it

Additional public source (Best Bias Discovery only): MAG Heat Relief Network, ArcGIS item bd08dde5206543018fe41da60d2551a7, "HRN Public view", https://services1.arcgis.com/MdyCMZnX1raZ7TS3/arcgis/rest/services/HRN_Public_view/FeatureServer/0 , retrieved 2026-09-27.

```bash
curl -s "https://services1.arcgis.com/MdyCMZnX1raZ7TS3/arcgis/rest/services/HRN_Public_view/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=geojson" -o extra/hrn.geojson
python heat_relief.py     # matching; writes extra/hrn_matched.csv and extra/hrn_tract_access.csv (keeps the audited sheet)
python audit_results.py   # final classes from the audited sheet; all tables and tests in section 2
```

The repository includes the audited sheet (`extra/hrn_audit.csv`, with an OpenStreetMap link per site for re-checking) and the layer snapshot (`extra/hrn.geojson`). Code: ⟨REPO LINK⟩

## 6. Limitations
- **Coverage over time.** The HRN layer is a live service; sites can change within a season. The copy used here was retrieved on 2026-09-27. The season opened on May 1, 2026, and the Overture release is dated 2026-08-19.
- **The audit is a judgment from names and places within 150 m.** Every decision is in the sheet, including the four borderline sites settled in section 2.2.
- **The 150 m radius** may miss a place pinned elsewhere on a large campus.
- **Operator type** is assigned from the organization name (city, town, county, library district = government).
- **Licence.** The HRN layer is public and anonymously queryable, but its item page carries an accuracy disclaimer, not an open licence. The repository includes a snapshot (retrieved 2026-09-27T17:20:26Z, sha256 a130c1f7…37d9) because the layer is seasonal and may change after September 30. The snapshot will be removed on request.

## Sources (all retrieved 2026-09-27)
- MAG Heat Relief Network, "HRN Public view": https://services1.arcgis.com/MdyCMZnX1raZ7TS3/arcgis/rest/services/HRN_Public_view/FeatureServer/0
- Maricopa County 2026 HRN launch: https://www.maricopa.gov/m/newsflash/Home/Detail/3652
- MCDPH Heat-Related Deaths Reports:
  - 2023: https://www.maricopa.gov/ArchiveCenter/ViewFile/Item/5820
  - 2024: https://www.maricopa.gov/ArchiveCenter/ViewFile/Item/5934
  - 2025: https://www.maricopa.gov/ArchiveCenter/ViewFile/Item/6510
- CDC MMWR 74(14): https://www.cdc.gov/mmwr/volumes/74/wr/mm7414a4.htm
- Overture place schema (no opening-hours property): https://docs.overturemaps.org/schema/reference/places/place/
- Overture categories (no cooling, heat-relief or hydration category): https://github.com/OvertureMaps/schema/blob/96ec26830d5b1c83216de3ce1a91c301c178705e/docs/schema/concepts/by-theme/places/overture_categories.csv
- Novelty check: no earlier comparison of official cooling-center lists with OSM, Overture or commercial maps was found. The closest work (arXiv:2410.09067) studies cooling-center coverage, not map data.
