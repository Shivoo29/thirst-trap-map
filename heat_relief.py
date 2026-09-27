"""Bias discovery: are Maricopa's official heat-relief sites findable on the open map?
Official list: MAG Heat Relief Network (extra/hrn.geojson, see extra/hrn.retrieved.txt).
Each site gets one status, from Overture places within RADIUS m:
  site     - a place whose name matches the site's name
  operator - only a place matching the operating organization's name
  absent   - neither
Then per tract: distance to the nearest official site vs the nearest site findable by name.
Writes extra/hrn_matched.csv and extra/hrn_tract_access.csv."""
import re
import geopandas as gpd
import numpy as np
import pandas as pd

RADIUS, JACCARD = 150, 0.6
UTM = 26912  # NAD83 / UTM 12N, metres
COUNTY = "04013"  # Maricopa County: the only county the Heat Relief Network covers
R = "data/reference/maricopa-az/maricopa-az"
S = "data/strata/maricopa-az/maricopa-az"
STOP = {"the", "of", "and", "at", "a", "az", "inc", "llc", "st"}
# Words that name a kind of facility, not a facility: two names sharing only these are not a match.
GENERIC = {"library", "clinic", "center", "health", "community", "service", "family", "recreation",
           "senior", "department", "public", "campus", "court", "main", "civic", "city"}


def tokens(s, city=""):
    s = re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).replace(city, " ")
    return {w[:-1] if len(w) > 3 and w.endswith("s") else w for w in s.split()} - STOP


def similar(a, b, city):
    """Token match with the site's city name removed (it is shared by every place nearby):
    Jaccard >= JACCARD, or one name's tokens contained in the other's with a non-generic token."""
    city = re.sub(r"[^a-z0-9 ]", " ", str(city).lower()).strip() or "\0"
    a, b = tokens(a, city), tokens(b, city)
    if not a or not b:
        return False
    small = min(a, b, key=len)
    return len(a & b) / len(a | b) >= JACCARD or (small <= (a & b) and bool(small - GENERIC))


# Self-check: false matches the first, looser matcher made, and true matches it must keep.
for a, b, city, want in [("Peoria Main Library", "Peoria Human Resources", "Peoria", False),
                         ("Queen Creek Library", "Queen Creek BBQ Co", "Queen Creek", False),
                         ("El Mirage Library", "El Mirage Fire Department", "El Mirage", False),
                         ("Venado Valley Health Center", "Deer Valley Medical Center", "Phoenix", False),
                         ("John F. Long Family Service Center", "John F. Long Family Services Center", "Phoenix", True),
                         ("Mesa Dining Room", "St Vincent Mesa Dining Room", "Mesa", True),
                         ("Mountain Park Tempe Clinic", "Mountain Park Health Center Tempe Clinic", "Tempe", True)]:
    assert similar(a, b, city) == want, (a, b)

hrn = gpd.read_file("extra/hrn.geojson")
hrn = hrn[hrn.HeatRelief == "Yes"].to_crs(UTM).reset_index(drop=True)

pois = gpd.read_parquet(f"{R}-overture-pois.parquet", columns=["names", "categories", "geometry"])
pois["name"] = pois.names.str["primary"]
pois["category"] = pois.categories.str["primary"]
pois = pois.drop(columns=["names", "categories"]).to_crs(UTM)

cand = gpd.sjoin(hrn[["Location", "Organization", "City"]].set_geometry(hrn.buffer(RADIUS)), pois, how="inner")
cand["site"] = [similar(a, b, c) for a, b, c in zip(cand.Location, cand.name, cand.City)]
cand["oper"] = [similar(a, b, c) for a, b, c in zip(cand.Organization, cand.name, cand.City)]
cand["dist_m"] = hrn.geometry.loc[cand.index].distance(pois.geometry.loc[cand.index_right], align=False).values
cand = cand.sort_values("dist_m")
site = cand[cand.site].groupby(level=0).agg(ov_name=("name", "first"), ov_cat=("category", "first"),
                                            ov_dist_m=("dist_m", "first"))
hrn = hrn.join(site)
oper_idx = set(cand[cand.oper].index)
hrn["status"] = np.where(hrn.ov_name.notna(), "site",
                         np.where(hrn.index.isin(oper_idx), "operator", "absent"))
# ponytail: government = public agency by name; everything else (faith, nonprofit, clinic, business)
hrn["org_kind"] = np.where(hrn.Organization.str.contains(r"City of|Town of|County|Library District", case=False),
                           "government", "nonprofit/faith/other")

tracts = gpd.read_parquet(f"{S}-census-tracts.parquet", columns=["GEOID", "geometry"]).to_crs(UTM)
strata = pd.read_parquet(f"{S}-strata-tract-table.parquet",
                         columns=["GEOID", "pop_total", "svi_overall", "hwd_heatindex_mean", "ur_class"])
hrn = gpd.sjoin(hrn, tracts, how="left", predicate="within").drop(columns="index_right").merge(strata, on="GEOID", how="left")
hrn[["Location", "Organization", "org_kind", "City", "HeatRelief_Type", "GEOID", "svi_overall",
     "status", "ov_name", "ov_cat"]].to_csv("extra/hrn_matched.csv", index=False)

# Audit sheet: one row per site for a human to confirm. Identical names (after normalization) are
# pre-marked auto-ok; everything else says REVIEW and sorts first.
ll = hrn.geometry.to_crs(4326)
exact = [m and tokens(a, c.lower()) == tokens(b, c.lower())
         for a, b, c, m in zip(hrn.Location, hrn.ov_name.fillna(""), hrn.City, hrn.status == "site")]
nearby = cand.groupby(level=0).apply(lambda g: "; ".join(
    f"{n} [{c}] {d:.0f}m" for n, c, d in zip(g["name"].head(4), g["category"].head(4), g["dist_m"].head(4))))
audit = pd.DataFrame({
    "suggested": np.where(exact, "auto-ok", "REVIEW"), "status": hrn.status,
    "type": hrn.HeatRelief_Type, "site": hrn.Location, "organization": hrn.Organization,
    "address": hrn.Address, "overture_match": hrn.ov_name, "overture_category": hrn.ov_cat,
    "match_dist_m": hrn.ov_dist_m.round(), "places_within_150m": nearby.reindex(hrn.index).fillna(""),
    "map": [f"https://www.openstreetmap.org/?mlat={p.y:.6f}&mlon={p.x:.6f}#map=19/{p.y:.6f}/{p.x:.6f}" for p in ll],
    "verdict": "", "note": ""})
import os
if os.path.exists("extra/hrn_audit.csv"):  # holds hand-filled verdicts: never overwrite
    print("extra/hrn_audit.csv exists, kept (delete it to regenerate a blank sheet)")
else:
    audit.sort_values(["suggested", "status"]).to_csv("extra/hrn_audit.csv", index_label="id")

# Access: from each tract's interior point, nearest official site vs nearest site findable by name.
pts = tracts[tracts.GEOID.str.startswith(COUNTY)]
pts = pts.assign(geometry=pts.representative_point()).merge(strata, on="GEOID")
pts["d_official_km"] = gpd.sjoin_nearest(pts, hrn[["geometry"]], distance_col="d").groupby(level=0).d.first() / 1000
pts["d_findable_km"] = gpd.sjoin_nearest(pts, hrn.loc[hrn.status == "site", ["geometry"]],
                                         distance_col="d").groupby(level=0).d.first() / 1000
pts["extra_km"] = pts.d_findable_km - pts.d_official_km
pts.drop(columns="geometry").to_csv("extra/hrn_tract_access.csv", index=False)


def wmean(g, col):
    return np.average(g[col], weights=g.pop_total) if g.pop_total.sum() else np.nan


if __name__ == "__main__":
    print(f"sites: {len(hrn)}")
    print(pd.crosstab(hrn.org_kind, hrn.status, normalize="index", margins=True).round(3))
    print(pd.crosstab(hrn.HeatRelief_Type, hrn.status, normalize="index").round(3))
    print("site-matched categories:", hrn.ov_cat.value_counts(dropna=False).to_dict())

    pop = pts[pts.pop_total > 0].copy()
    pop["svi_q"] = pd.qcut(pop.svi_overall, 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    pop["heat_q"] = pd.qcut(pop.hwd_heatindex_mean.rank(method="first"), 4, labels=["H1 cool", "H2", "H3", "H4 hot"])
    for g in ["svi_q", "heat_q", "ur_class"]:
        t = pop.groupby(g, observed=True).apply(lambda x: pd.Series({
            "tracts": len(x), "pop": x.pop_total.sum(),
            "official_km": wmean(x, "d_official_km"), "findable_km": wmean(x, "d_findable_km"),
            "extra_km": wmean(x, "extra_km"),
            "share_pop_extra_gt_1km": np.average(x.extra_km > 1, weights=x.pop_total)}), include_groups=False)
        print(t.round(3))
