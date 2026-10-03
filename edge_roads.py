"""Road lengths inside each tract and along its edge, from Overture roads and tract polygons only.
Tract boundaries often run along highways. A highway drawn on the boundary counts for the tracts
on both sides, but Overture's line sits a few metres off it, inside one tract only. So a tract whose
edge highway lies just outside it looks like it has no highway of its own.
Output: edge_roads.parquet, per GEOID and road kind: km_<kind>_in (inside) and km_<kind>_edge
(outside, within EDGE_M of the boundary, pieces longer than MIN_PIECE_M so crossing roads don't
count). Kinds: named (Overture motorway/trunk/primary/secondary), route (state-level route network,
see STATE_ROUTE), fm (Texas FM/RM), county (county route networks), nonet (route with no network).
All lengths in EPSG:5070."""
import sys

import duckdb

from features import D, REGIONS, STATE_ROUTE

EDGE_M, MIN_PIECE_M = 30, 100
NAMED = "('motorway','trunk','primary','secondary')"
FM = r"^US:TX:(FM|RM)$"
COUNTY = r"^US:[A-Z]{2}:(CR|[A-Z][a-z]+)$"
NOT_COUNTY = "('Scenic','Historic','Loop','Spur','Business','Beltway','Bypass','Truck','Alternate','Turnpike','BDR','Old')"
KINDS = ["named", "route", "fm", "county", "nonet"]

con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")


def has(pred):
    return f"coalesce(len(list_filter(routes, x -> {pred})), 0) > 0"


def region_sql(r):
    ref, st = f"{D}/reference/{r}/{r}", f"{D}/strata/{r}/{r}"
    net = "coalesce(x.network, '')"
    aggs = ",\n           ".join(
        f"coalesce(sum(in_m) FILTER (WHERE {k}), 0) / 1000 km_{k}_in,\n           "
        f"coalesce(sum(edge_m) FILTER (WHERE {k} AND edge_m > {MIN_PIECE_M}), 0) / 1000 km_{k}_edge"
        for k in KINDS)
    return f"""
    WITH tr AS (
        SELECT GEOID, ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true) g
        FROM '{st}-census-tracts.parquet'),
    ring AS (SELECT GEOID, g, ST_Difference(ST_Buffer(g, {EDGE_M}), g) ring FROM tr),
    rd AS (
        SELECT ST_Transform(geometry, 'EPSG:4326', 'EPSG:5070', always_xy := true) g,
               class IN {NAMED} named,
               {has(f"regexp_matches({net}, '{STATE_ROUTE}')")} route,
               {has(f"regexp_matches({net}, '{FM}')")} fm,
               {has(f"regexp_matches({net}, '{COUNTY}') AND split_part(x.network, ':', 3) NOT IN {NOT_COUNTY}")} county,
               {has("x.network IS NULL")} nonet
        FROM '{ref}-overture-roads.parquet'),
    pieces AS (
        SELECT t.GEOID, r.* EXCLUDE g,
               ST_Length(ST_Intersection(r.g, t.g)) in_m,
               ST_Length(ST_Intersection(r.g, t.ring)) edge_m
        FROM rd r JOIN ring t ON ST_Intersects(ST_Buffer(t.g, {EDGE_M}), r.g)
        WHERE {" OR ".join(f"r.{k}" for k in KINDS)})
    SELECT GEOID,
           {aggs}
    FROM pieces GROUP BY 1
    """


if __name__ == "__main__":
    regions = sys.argv[1:] or REGIONS
    df = con.sql(" UNION ALL ".join(f"({region_sql(r)})" for r in regions)).df()
    out = "edge_roads.parquet" if len(regions) == len(REGIONS) else f"edge_roads-{'_'.join(regions)}.parquet"
    df.to_parquet(out, index=False)
    print(df.shape, "->", out)
