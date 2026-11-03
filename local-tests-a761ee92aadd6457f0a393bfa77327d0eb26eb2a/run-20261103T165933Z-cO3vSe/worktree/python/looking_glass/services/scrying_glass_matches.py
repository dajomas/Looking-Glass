"""Expand a validated campaign/room result to exact and hyphen-boundary variants."""
def expand_matches(result, payload):
    out = {**result, "setup_names": [], "match_count": 0, "exact_match": False}
    # Preserve validation/access/ambiguity outcomes from the existing matcher.
    if result.get("status") not in {"matched", "setup_not_found"}:
        return out
    slug = result.get("setup_name", "")
    if not slug:
        return out
    campaign = next(c for c in payload["campaigns"]
                    if str(c.get("id")) == result["campaign_id"]
                    and c["name"].strip() == result["campaign_name"].strip())
    prefix = slug + "-"
    names = sorted({name for name in campaign["setups"]
                    if name == slug or (name.startswith(prefix) and len(name) > len(prefix))},
                   key=lambda name: (name != slug, name.casefold(), name))
    count = len(names)
    message = (f"Matching battle setup found: {names[0]}." if count == 1 else
               f"{count} matching battle setups found." if count else
               f"No battle setup matches room prefix {slug} in the matching campaign.")
    return {**out, "matched": bool(names), "status": "matched" if names else "setup_not_found",
            "setup_names": names, "match_count": count, "exact_match": slug in names, "message": message}
