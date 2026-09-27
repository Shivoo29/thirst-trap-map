"""Final findability table from the hand-audited sheet extra/hrn_audit.csv.
Classes: by_name (the site's own name finds it), generic_name (only an operator, system,
old or host name is on the map), absent, unsure."""
from math import comb

import pandas as pd

VERDICT = {"auto-ok": "by_name", "ok": "by_name", "operator_ok": "generic_name",
           "other_name": "generic_name", "absent": "absent", "wrong_match": "absent", "unsure": "unsure"}
# Rulings on first-pass verdicts (id -> class, reason).
RULINGS = {
    63: ("by_name", "Escalante Multi-Generational Center: same name, hyphen"),
    135: ("by_name", "North Tempe Multi-Generational Center: same name, hyphen"),
    141: ("by_name", "Glendale Mission And Ministry Center: same name, '&'"),
    74: ("by_name", "'Salvation Army Estrella Mountain' carries the site name"),
    208: ("by_name", "'Copa Health - East Valley' carries the site name"),
    224: ("by_name", "'Adelante Healthcare Goodyear' carries the site name"),
    184: ("generic_name", "'Scottsdale Public Library' at 0 m is the Civic Center branch"),
}


def fisher_p(a, n1, c, n2):
    """Two-sided Fisher exact test for a/n1 vs c/n2 (stdlib only)."""
    k, n = a + c, n1 + n2
    p = lambda x: comb(n1, x) * comb(n2, k - x) / comb(n, k)
    return sum(p(x) for x in range(max(0, k - n2), min(k, n1) + 1) if p(x) <= p(a) * (1 + 1e-9))


assert abs(fisher_p(27, 119, 1, 119) - 4.6e-8) < 1e-8  # value computed earlier in this project

a = pd.read_csv("extra/hrn_audit.csv")
a["final"] = a.verdict.fillna(a.suggested).map(VERDICT)
for i, (cls, _) in RULINGS.items():
    a.loc[a.id == i, "final"] = cls
a["org_kind"] = a.organization.str.contains(r"City of|Town of|County|Library District", case=False) \
    .map({True: "government", False: "nonprofit/faith/other"})
a.to_csv("extra/hrn_final.csv", index=False)

if __name__ == "__main__":
    t = pd.crosstab(a.org_kind, a.final, margins=True)
    print(t, "\n")
    print((pd.crosstab(a.org_kind, a.final, normalize="index") * 100).round(1), "\n")
    print((pd.crosstab(a.type, a.final, normalize="index") * 100).round(1), "\n")

    # The three comparisons tested (Bonferroni x3), unsure rows excluded.
    svi = pd.read_csv("extra/hrn_matched.csv").svi_overall  # row i = site id i
    s = a[a.final != "unsure"].assign(svi=lambda d: d.id.map(svi))
    s["q4"] = s.svi >= s.svi.quantile(0.75)
    absent, generic, hyd, gov = s.final == "absent", s.final == "generic_name", s.type == "Hydration Station", s.org_kind == "government"
    for name, hit, grp in [("absent: hydration vs cooling+respite", absent, hyd),
                           ("absent: SVI top quartile vs rest", absent, s.q4),
                           ("generic_name: nonprofit vs government", generic, ~gov)]:
        a1, n1, c1, n2 = hit[grp].sum(), grp.sum(), hit[~grp].sum(), (~grp).sum()
        p = fisher_p(a1, n1, c1, n2)
        print(f"{name}: {a1}/{n1} ({a1/n1:.1%}) vs {c1}/{n2} ({c1/n2:.1%}), p={p:.2g}, x3={min(1, 3*p):.2g}")
    h = s[hyd]
    print(f"hydration stations absent, SVI top quartile: {(h.final[h.q4] == 'absent').sum()}/{h.q4.sum()}, "
          f"rest: {(h.final[~h.q4] == 'absent').sum()}/{(~h.q4).sum()}")
    print("\ngeneric_name by operator:", a[a.final == "generic_name"].organization.value_counts().to_dict())
    print("unsure ids:", a[a.final == "unsure"].id.tolist())
