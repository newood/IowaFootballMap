#!/usr/bin/env python3
"""Maps of IHSAA 11-player football districts/groups for the 2025-26 cycle.

Towns are U.S. Census Bureau internal points (2023 Gazetteer) unless a
campus coordinate is stored on the school. Zones are each district's convex
hull, expanded and clipped to Iowa. They are a visual span, not an official
IHSAA boundary.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import shapely
from matplotlib import font_manager
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MPath
from shapely.geometry import Point, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CLASS_DIR = DATA / "classes"
OUT = ROOT / "output"
CLASS_ORDER = ["5A", "4A", "3A", "2A", "1A", "A"]

LON0 = -93.6
LAT0 = 42.0
MILES_PER_DEG_LAT = 69.172
COS_LAT = math.cos(math.radians(LAT0))
BUFFER_MI = 12.0
BUFFER_BY_CLASS = {"5A": 8.0}

COLORS = {
    1: "#1D4E89",
    2: "#C65D00",
    3: "#1B7A43",
    4: "#6C3483",
    5: "#AD2E5C",
    6: "#7A4E12",
    7: "#0F6E6E",
    8: "#B33228",
}


def to_xy(lon: float, lat: float) -> tuple[float, float]:
    return ((lon - LON0) * MILES_PER_DEG_LAT * COS_LAT, (lat - LAT0) * MILES_PER_DEG_LAT)


def miles_between(lon1, lat1, lon2, lat2) -> float:
    x1, y1 = to_xy(lon1, lat1)
    x2, y2 = to_xy(lon2, lat2)
    return math.hypot(x2 - x1, y2 - y1)


def project_geom(geom):
    return transform(lambda lon, lat, z=None: to_xy(lon, lat), geom)


def unproject_geom(geom):
    def inv(x, y, z=None):
        return (x / (MILES_PER_DEG_LAT * COS_LAT) + LON0, y / MILES_PER_DEG_LAT + LAT0)

    return transform(inv, geom)


def load_places(path: Path) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    with path.open() as handle:
        header = [h.strip() for h in handle.readline().split("\t")]
        for line in handle:
            parts = [p.strip() for p in line.rstrip("\n").split("\t")]
            if len(parts) < len(header):
                continue
            row = dict(zip(header, parts))
            if row["USPS"] != "IA":
                continue
            raw = row["NAME"]
            if raw.endswith(" city"):
                base = raw[: -len(" city")]
            elif raw.endswith(" CDP"):
                base = raw[: -len(" CDP")]
            else:
                base = raw
            index.setdefault(base, []).append(row)
    return index


def lookup_place(index: dict, name: str) -> tuple[float, float]:
    rows = index.get(name)
    if not rows:
        raise SystemExit(f"Census gazetteer has no Iowa place named {name!r}")
    rows = sorted(rows, key=lambda r: (r["LSAD"] != "25", -float(r["ALAND"])))
    row = rows[0]
    return float(row["INTPTLONG"]), float(row["INTPTLAT"])


def load_counties(path: Path):
    data = json.loads(path.read_text())
    counties = []
    for feature in data["features"]:
        geom = shape(feature["geometry"])
        counties.append(
            {
                "name": feature["properties"]["NAME"],
                "geom_ll": geom,
                "geom": project_geom(geom),
            }
        )
    return counties


def county_of(lon: float, lat: float, counties) -> str:
    point = Point(lon, lat)
    nearest_name = None
    nearest = 1e9
    for county in counties:
        if county["geom_ll"].covers(point):
            return county["name"]
        distance = county["geom_ll"].distance(point)
        if distance < nearest:
            nearest = distance
            nearest_name = county["name"]
    if nearest < 0.04:
        return nearest_name
    raise SystemExit(f"Point {lat:.4f}, {lon:.4f} is not inside Iowa ({nearest_name}, {nearest:.3f} deg)")


def polygonal(geom):
    if geom.is_empty:
        return shapely.Polygon()
    if geom.geom_type in ("Polygon", "MultiPolygon"):
        return geom
    parts = []
    for part in getattr(geom, "geoms", []):
        if part.geom_type in ("Polygon", "MultiPolygon"):
            parts.append(part)
    return shapely.union_all(parts) if parts else shapely.Polygon()


def iter_polygons(geom):
    if geom.is_empty:
        return
    if geom.geom_type == "Polygon":
        yield geom
    elif geom.geom_type == "MultiPolygon":
        yield from geom.geoms
    elif geom.geom_type == "GeometryCollection":
        for part in geom.geoms:
            yield from iter_polygons(part)


def polygon_patch(poly, **kwargs) -> PathPatch:
    vertices = []
    codes = []

    def add_ring(ring):
        coords = list(ring.coords)
        vertices.extend(coords)
        codes.append(MPath.MOVETO)
        codes.extend([MPath.LINETO] * (len(coords) - 2))
        codes.append(MPath.CLOSEPOLY)

    add_ring(poly.exterior)
    for hole in poly.interiors:
        add_ring(hole)
    return PathPatch(MPath(vertices, codes), **kwargs)


def compass(dx: float, dy: float) -> str:
    if abs(dx) < 0.4 and abs(dy) < 0.4:
        return "at the same place"
    ns = "north" if dy > 0.4 else "south" if dy < -0.4 else ""
    ew = "east" if dx > 0.4 else "west" if dx < -0.4 else ""
    return f"{ns}{ew}"


def region_for(lon: float, lat: float) -> str:
    ns = "north" if lat >= 42.55 else "south" if lat <= 41.55 else "central"
    ew = "west" if lon <= -94.7 else "east" if lon >= -92.3 else "central"
    return {
        ("north", "west"): "Northwest",
        ("north", "central"): "North-central",
        ("north", "east"): "Northeast",
        ("central", "west"): "West-central",
        ("central", "central"): "Central",
        ("central", "east"): "East-central",
        ("south", "west"): "Southwest",
        ("south", "central"): "South-central",
        ("south", "east"): "Southeast",
    }[(ns, ew)]


def load_class_specs(only: list[str] | None = None) -> list[dict]:
    wanted = only or CLASS_ORDER
    unknown = [item for item in wanted if item not in CLASS_ORDER]
    if unknown:
        raise SystemExit(f"Unknown class id(s): {', '.join(unknown)}")
    specs = []
    for class_id in wanted:
        path = CLASS_DIR / f"{class_id}.json"
        if not path.exists():
            raise SystemExit(f"Missing class dataset {path}")
        specs.append(json.loads(path.read_text()))
    return specs


def build_records(spec, places, counties):
    records = []
    for item in spec["teams"]:
        towns = []
        for place_item in item["places"]:
            gazetteer_name = place_item["gazetteer"]
            display = place_item["display"]
            if "lon" in place_item and "lat" in place_item:
                lon, lat = float(place_item["lon"]), float(place_item["lat"])
            else:
                lon, lat = lookup_place(places, gazetteer_name)
            county = county_of(lon, lat, counties)
            x, y = to_xy(lon, lat)
            towns.append(
                {
                    "gazetteer": gazetteer_name,
                    "display": display,
                    "lon": lon,
                    "lat": lat,
                    "county": county,
                    "x": x,
                    "y": y,
                }
            )
        records.append(
            {
                "district": int(item["district"]),
                "school": item["school"],
                "towns": towns,
                "map_label": item.get("map_label"),
            }
        )
    return records


def district_ids(records) -> list[int]:
    return sorted({record["district"] for record in records})


def regions_for(records) -> dict[int, str]:
    regions = {}
    for district in district_ids(records):
        towns = [town for record in records if record["district"] == district for town in record["towns"]]
        lon = sum(town["lon"] for town in towns) / len(towns)
        lat = sum(town["lat"] for town in towns) / len(towns)
        regions[district] = region_for(lon, lat)
    return regions


def check_records(spec, records, places):
    ids = district_ids(records)
    if not ids:
        raise SystemExit(f"{spec['id']} has no teams")
    by_district: dict[int, list] = {d: [] for d in ids}
    for record in records:
        by_district[record["district"]].append(record)
    counts = [len(group) for group in by_district.values()]
    if min(ids) != 1 or ids != list(range(1, max(ids) + 1)):
        raise SystemExit(f"{spec['id']} district numbers are not a 1..n sequence: {ids}")
    if len(records) != len(spec["teams"]):
        raise SystemExit(f"{spec['id']} expected {len(spec['teams'])} teams, found {len(records)}")
    names = [record["school"] for record in records]
    if len(names) != len(set(names)):
        raise SystemExit(f"{spec['id']} has duplicate school names")

    facts = {"team_counts": counts}
    if spec["id"] == "1A":
        facts.update(check_1a(records, places))
    return facts


def check_1a(records, places):
    by_school = {record["school"]: record for record in records}
    clarion = by_school["Clarion-Goldfield-Dows"]["towns"][0]
    eagle = by_school["Eagle Grove"]["towns"][0]
    if clarion["county"] != "Wright" or eagle["county"] != "Wright":
        raise SystemExit(
            f"Clarion is in {clarion['county']}, Eagle Grove is in {eagle['county']}; both should be Wright"
        )
    dx = eagle["x"] - clarion["x"]
    dy = eagle["y"] - clarion["y"]
    distance = math.hypot(dx, dy)
    direction = compass(dx, dy)
    if direction != "southwest" or not (7 <= distance <= 15):
        raise SystemExit(
            f"Eagle Grove should be about 10 miles southwest of Clarion, got {distance:.1f} miles {direction}"
        )
    inwood = by_school["West Lyon"]["towns"][0]
    if inwood["county"] != "Lyon" or inwood["lat"] < 43.15 or inwood["lon"] > -96.2:
        raise SystemExit(f"West Lyon / Inwood looks wrong: {inwood}")
    return {
        "eagle_miles": distance,
        "eagle_direction": direction,
        "clarion_county": clarion["county"],
    }


def choose_font() -> str:
    available = {font.name for font in font_manager.fontManager.ttflist}
    for name in ("Avenir Next", "Avenir", "Helvetica Neue", "Helvetica", "Arial"):
        if name in available:
            return name
    return "DejaVu Sans"


def zone_for(record_group, state, buffer_mi: float = BUFFER_MI):
    points = [Point(town["x"], town["y"]) for record in record_group for town in record["towns"]]
    hull = shapely.MultiPoint(points).convex_hull
    widened = hull.buffer(buffer_mi, resolution=16, join_style=1)
    return polygonal(widened.intersection(state))


def badge_anchor(zone, avoid_points, preferred_xy):
    preferred = Point(*preferred_xy)
    if zone.covers(preferred):
        clearance = min(preferred.distance(point) for point in avoid_points)
        if clearance >= 10:
            return (preferred.x, preferred.y)
    minx, miny, maxx, maxy = zone.bounds
    best = None
    best_score = -1e9
    step = 3.0
    x = minx
    while x <= maxx:
        y = miny
        while y <= maxy:
            point = Point(x, y)
            if zone.covers(point):
                clearance = min(point.distance(other) for other in avoid_points)
                score = clearance * 2.0 - point.distance(preferred)
                if score > best_score:
                    best_score = score
                    best = (x, y)
            y += step
        x += step
    if best is None:
        rep = zone.representative_point()
        return (rep.x, rep.y)
    return best


def draw_rings(ax, geom, **plot_kwargs):
    for poly in iter_polygons(geom):
        xs, ys = poly.exterior.xy
        ax.plot(xs, ys, **plot_kwargs)
        for hole in poly.interiors:
            hxs, hys = hole.xy
            ax.plot(hxs, hys, **plot_kwargs)


def word_number(n: int) -> str:
    words = {6: "SIX", 7: "SEVEN", 8: "EIGHT", 10: "TEN"}
    return words.get(n, str(n))


def draw_map(spec, records, counties, regions, font_name: str):
    state = unary_union([county["geom"].buffer(0.25) for county in counties])
    state = polygonal(state)
    ids = district_ids(records)
    unit = spec["unit"]

    zones = {}
    buffer_mi = BUFFER_BY_CLASS.get(spec["id"], BUFFER_MI)
    for district in ids:
        group = [record for record in records if record["district"] == district]
        zones[district] = zone_for(group, state, buffer_mi)

    fig = plt.figure(figsize=(23.6, 15.4), dpi=140, facecolor="#efeae3")
    ax = fig.add_axes([0.018, 0.078, 0.668, 0.785])
    roster = fig.add_axes([0.698, 0.078, 0.286, 0.785])
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_facecolor("#e3ddd2")
    roster.set_axis_off()
    roster.set_xlim(0, 1)
    roster.set_ylim(0, 1)
    roster.set_facecolor("#efeae3")

    for poly in iter_polygons(state):
        ax.add_patch(polygon_patch(poly, facecolor="#fbf9f4", edgecolor="none", zorder=0))

    for district, zone in zones.items():
        color = COLORS[district]
        for poly in iter_polygons(zone):
            ax.add_patch(polygon_patch(poly, facecolor=color, edgecolor="none", alpha=0.30, zorder=1))
        draw_rings(ax, zone, color=color, lw=1.7, solid_capstyle="round", solid_joinstyle="round", zorder=3)

    for county in counties:
        draw_rings(ax, county["geom"], color="#8a847a", lw=0.38, zorder=2, alpha=0.8)

    draw_rings(ax, state, color="#241f1a", lw=1.25, zorder=3)

    minx, miny, maxx, maxy = state.bounds
    pad_x, pad_y = 28, 22
    ax.set_xlim(minx - pad_x, maxx + pad_x)
    ax.set_ylim(miny - pad_y, maxy + pad_y)

    def spaced(text: str) -> str:
        return " ".join(text)

    cx = (minx + maxx) / 2
    neighbor_style = dict(fontsize=8.5, color="#a39c90", fontfamily=font_name, zorder=3, clip_on=False)
    ax.text(cx, maxy + 8, spaced("MINNESOTA"), ha="center", va="bottom", **neighbor_style)
    ax.text(cx, miny - 8, spaced("MISSOURI"), ha="center", va="top", **neighbor_style)
    ax.text(minx - 6, (miny + maxy) / 2 - 38, spaced("NEBRASKA"), ha="right", va="center", rotation=90, **neighbor_style)
    ax.text(minx - 6, maxy - 28, spaced("SOUTH DAKOTA"), ha="right", va="center", rotation=90, **neighbor_style)
    ax.text(maxx + 7, (miny + maxy) / 2 - 8, spaced("ILLINOIS"), ha="left", va="center", rotation=90, **neighbor_style)
    ax.text(maxx + 7, maxy - 18, spaced("WISCONSIN"), ha="left", va="center", rotation=90, **neighbor_style)

    for record in records:
        color = COLORS[record["district"]]
        towns = record["towns"]
        if len(towns) == 2:
            ax.plot(
                [towns[0]["x"], towns[1]["x"]],
                [towns[0]["y"], towns[1]["y"]],
                color=color,
                lw=1.25,
                zorder=5,
                solid_capstyle="round",
            )
        for town in towns:
            ax.scatter(
                [town["x"]],
                [town["y"]],
                s=210,
                facecolor=color,
                edgecolor="white",
                linewidths=1.05,
                zorder=6,
            )
            ax.text(
                town["x"],
                town["y"],
                str(record["district"]),
                ha="center",
                va="center",
                fontsize=6.4,
                fontweight="bold",
                color="white",
                zorder=7,
                fontfamily=font_name,
            )

    texts = []
    target_x = []
    target_y = []
    for record in records:
        towns = record["towns"]
        group = [item for item in records if item["district"] == record["district"]]
        all_towns = [town for item in group for town in item["towns"]]
        gx = sum(town["x"] for town in all_towns) / len(all_towns)
        gy = sum(town["y"] for town in all_towns) / len(all_towns)
        if record["map_label"] is None:
            labeled = [(town, town["display"]) for town in towns]
        else:
            labeled = [(towns[0], record["map_label"])]
        for town, label in labeled:
            dx, dy = town["x"] - gx, town["y"] - gy
            norm = math.hypot(dx, dy) or 1.0
            ox, oy = dx / norm * 8.0, dy / norm * 6.5
            text = ax.text(
                town["x"] + ox,
                town["y"] + oy,
                label,
                ha="center",
                va="center",
                fontsize=7.05,
                color="#1b1b1b",
                zorder=8,
                fontfamily=font_name,
                linespacing=0.95,
                path_effects=[pe.withStroke(linewidth=3.0, foreground="#fbf9f4")],
            )
            texts.append(text)
            target_x.append(town["x"])
            target_y.append(town["y"])

    all_school_points = [Point(town["x"], town["y"]) for record in records for town in record["towns"]]
    badges = []
    for district, zone in zones.items():
        towns = [town for record in records if record["district"] == district for town in record["towns"]]
        preferred = (sum(town["x"] for town in towns) / len(towns), sum(town["y"] for town in towns) / len(towns))
        bx, by = badge_anchor(zone, all_school_points, preferred)
        nearest = min(math.hypot(bx - point.x, by - point.y) for point in all_school_points)
        print(
            f"{spec['id']} badge {unit} {district}: ({bx:.0f}, {by:.0f}) miles from origin, "
            f"{nearest:.0f} mi from nearest school, inside={zone.covers(Point(bx, by))}"
        )
        badge = ax.text(
            bx,
            by,
            f"{unit.upper()} {district}",
            ha="center",
            va="center",
            fontsize=8.2,
            fontweight="bold",
            color="white",
            zorder=5,
            fontfamily=font_name,
            bbox=dict(boxstyle="round,pad=0.32", fc=COLORS[district], ec="white", lw=0.9),
        )
        badges.append(badge)

    x0 = minx - pad_x + 8
    y0 = miny - pad_y + 8
    ax.plot([x0, x0 + 50], [y0, y0], color="#241f1a", lw=2.0, solid_capstyle="butt", zorder=9, clip_on=False)
    ax.plot([x0, x0], [y0 - 1.3, y0 + 1.3], color="#241f1a", lw=1.1, zorder=9, clip_on=False)
    ax.plot([x0 + 50, x0 + 50], [y0 - 1.3, y0 + 1.3], color="#241f1a", lw=1.1, zorder=9, clip_on=False)
    ax.text(x0 + 25, y0 + 2.4, "50 miles", ha="center", va="bottom", fontsize=8, color="#241f1a", fontfamily=font_name, zorder=9, clip_on=False)
    nx = maxx + pad_x - 14
    ny = maxy + pad_y - 20
    ax.annotate(
        "",
        xy=(nx, ny + 12),
        xytext=(nx, ny),
        arrowprops=dict(arrowstyle="-|>", color="#241f1a", lw=1.3),
        zorder=9,
        clip_on=False,
    )
    ax.text(nx, ny + 13.2, "N", ha="center", va="bottom", fontsize=11, fontweight="bold", color="#241f1a", fontfamily=font_name, zorder=9, clip_on=False)

    from adjustText import adjust_text

    adjust_text(
        texts,
        x=target_x,
        y=target_y,
        target_x=target_x,
        target_y=target_y,
        objects=badges,
        ax=ax,
        arrowprops=dict(arrowstyle="-", color="#5c574e", lw=0.55),
        force_text=(0.3, 0.55),
        force_static=(0.45, 0.8),
        force_explode=(0.15, 0.35),
        force_pull=(0.05, 0.08),
        expand=(1.12, 1.25),
        max_move=(7, 7),
        ensure_inside_axes=True,
        expand_axes=False,
        min_arrow_len=8,
        time_lim=5,
        iter_lim=200,
    )

    draw_roster(roster, spec, records, regions, font_name)

    n_districts = len(ids)
    sizes = sorted({len([r for r in records if r["district"] == d]) for d in ids})
    if len(sizes) == 1:
        size_text = f"{sizes[0]} teams each"
    else:
        size_text = " or ".join(str(s) for s in sizes) + " teams each"
    unit_word = f"{unit.lower()}s"
    fig.text(
        0.02,
        0.955,
        f"Iowa {spec['label']} Football",
        fontsize=26,
        fontweight="bold",
        color="#1c1c1c",
        fontfamily=font_name,
        va="top",
    )
    fig.text(
        0.02,
        0.912,
        f"2025–26 IHSAA {unit_word}    ·    {len(records)} schools    ·    {n_districts} {unit_word}    ·    {size_text}",
        fontsize=12.5,
        color="#3a3834",
        fontfamily=font_name,
        va="top",
    )
    fig.text(
        0.02,
        0.882,
        f"Dots sit on the actual towns. The number is the {unit.lower()}. Shading is the span of that {unit.lower()}’s schools, not an official boundary.",
        fontsize=10,
        color="#5c574e",
        fontfamily=font_name,
        va="top",
    )
    source_line = (
        "Town locations: U.S. Census Bureau 2023 Gazetteer internal points, with campus points for cities that have more than one high school. "
        "Assignments: IHSAA football districts and 5A groups released March 5, 2025, for the 2025 and 2026 seasons."
    )
    fig.text(0.02, 0.022, source_line, fontsize=7.6, color="#6a655d", fontfamily=font_name, va="center")

    OUT.mkdir(parents=True, exist_ok=True)
    slug = spec["id"].lower()
    png = OUT / f"iowa-class-{slug}-football-{unit_word}-2025-26.png"
    pdf = OUT / f"iowa-class-{slug}-football-{unit_word}-2025-26.pdf"
    fig.savefig(png, dpi=140, facecolor=fig.get_facecolor())
    fig.savefig(pdf, facecolor=fig.get_facecolor())
    plt.close(fig)
    return png, pdf, zones, state


def draw_roster(ax, spec, records, regions, font_name: str):
    ids = district_ids(records)
    n = len(ids)
    max_teams = max(len([r for r in records if r["district"] == d]) for d in ids)
    unit = spec["unit"]
    ax.add_patch(Rectangle((0.0, 0.0), 1.0, 1.0, facecolor="#fffcf8", edgecolor="#e0d9cc", linewidth=0.8, transform=ax.transAxes, zorder=0))
    ax.text(0.04, 0.985, f"{word_number(n)} {unit.upper()}S", ha="left", va="top", fontsize=11, fontweight="bold", color="#1c1c1c", fontfamily=font_name)
    ax.text(0.04, 0.962, "School on the left, town where the dot sits on the right.", ha="left", va="top", fontsize=7.3, color="#6d675e", fontfamily=font_name)

    top = 0.945
    height = top / n
    name_size = 6.55 if max_teams >= 7 else 7.15
    line = 0.0106 if max_teams >= 7 else 0.0124
    for district in ids:
        bottom = top - district * height
        color = COLORS[district]
        group = [record for record in records if record["district"] == district]
        ax.add_patch(Rectangle((0.03, bottom + 0.008), 0.012, height - 0.016, facecolor=color, edgecolor="none", transform=ax.transAxes, zorder=1))
        header_y = bottom + height - 0.012
        ax.text(0.06, header_y, f"{unit.upper()} {district}", ha="left", va="top", fontsize=9.0, fontweight="bold", color=color, fontfamily=font_name, transform=ax.transAxes)
        ax.text(0.97, header_y, f"{len(group)} teams", ha="right", va="top", fontsize=7.2, color="#8a847a", fontfamily=font_name, transform=ax.transAxes)
        ax.text(0.06, header_y - 0.016, regions[district], ha="left", va="top", fontsize=7.0, color="#5e5a54", fontfamily=font_name, transform=ax.transAxes)
        group.sort(key=lambda record: -max(town["lat"] for town in record["towns"]))
        for index, record in enumerate(group):
            y = header_y - 0.032 - index * line
            towns = " & ".join(town["display"] for town in record["towns"])
            ax.text(0.06, y, record["school"], ha="left", va="top", fontsize=name_size, color="#1c1c1c", fontfamily=font_name, transform=ax.transAxes)
            ax.text(0.97, y, towns, ha="right", va="top", fontsize=name_size, color="#6d675e", fontfamily=font_name, transform=ax.transAxes)


def class_payload(spec, records, regions, zones):
    district_features = []
    for district, zone in zones.items():
        district_features.append(
            {
                "type": "Feature",
                "properties": {
                    "district": district,
                    "region": regions[district],
                    "color": COLORS[district],
                    "unit": spec["unit"],
                },
                "geometry": mapping(unproject_geom(zone)),
            }
        )
    schools = []
    for record in records:
        for town in record["towns"]:
            schools.append(
                {
                    "district": record["district"],
                    "region": regions[record["district"]],
                    "school": record["school"],
                    "town": town["display"],
                    "county": town["county"],
                    "lat": town["lat"],
                    "lon": town["lon"],
                    "color": COLORS[record["district"]],
                    "shared": len(record["towns"]) > 1,
                }
            )
    ids = district_ids(records)
    sizes = sorted({len([r for r in records if r["district"] == d]) for d in ids})
    unit = spec["unit"]
    unit_word = f"{unit.lower()}s"
    if len(sizes) == 1:
        size_text = f"{sizes[0]} teams each"
    else:
        size_text = " or ".join(str(s) for s in sizes) + " teams each"
    return {
        "id": spec["id"],
        "label": spec["label"],
        "unit": unit,
        "summary": f"{len(records)} schools, {len(ids)} {unit_word}, {size_text}. Click a school to find it on the map. Click a {unit.lower()} heading to hide it.",
        "zones": {"type": "FeatureCollection", "features": district_features},
        "schools": schools,
        "colors": {str(k): v for k, v in COLORS.items() if k in ids},
        "regions": {str(k): v for k, v in regions.items()},
        "districts": ids,
    }


def write_csv(rows):
    path = OUT / "schools.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["class", "district", "unit", "region", "school", "town", "county", "latitude", "longitude"])
        writer.writerows(rows)
    return path


def write_html(counties, class_payloads):
    county_features = []
    for county in counties:
        county_features.append(
            {
                "type": "Feature",
                "properties": {"name": county["name"]},
                "geometry": mapping(county["geom_ll"]),
            }
        )
    payload = {
        "counties": {"type": "FeatureCollection", "features": county_features},
        "order": [item["id"] for item in class_payloads],
        "classes": {item["id"]: item for item in class_payloads},
    }
    html = HTML_TEMPLATE.replace("/*__DATA__*/", json.dumps(payload))
    path = OUT / "iowa-football-districts-2025-26.html"
    path.write_text(html)
    legacy = OUT / "iowa-class-1a-football-districts-2025-26.html"
    legacy.write_text(html)
    (ROOT / "index.html").write_text(html)
    return path


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Iowa High School Football Districts, 2025–26</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<style>
  html, body { margin: 0; height: 100%; font-family: "Avenir Next", "Helvetica Neue", Helvetica, Arial, sans-serif; color: #1c1c1c; }
  #map { position: absolute; inset: 0; }
  #panel {
    position: absolute; top: 16px; right: 16px; width: 320px; max-height: calc(100% - 32px);
    overflow: auto; background: rgba(255,252,248,0.96); border: 1px solid #e0d9cc;
    border-radius: 10px; padding: 14px 14px 10px; box-shadow: 0 8px 28px rgba(40,30,10,0.12); z-index: 500;
  }
  .toolbar { display: flex; align-items: center; gap: 8px; margin: 0 0 10px; }
  .toolbar label { font-size: 11px; color: #6d675e; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
  #class-select {
    flex: 1; font: inherit; font-size: 14px; font-weight: 600; color: #1c1c1c;
    border: 1px solid #d9d0c2; border-radius: 8px; background: #fff; padding: 6px 8px;
  }
  h1 { font-size: 18px; margin: 0 0 4px; }
  .sub { font-size: 12px; color: #5c574e; margin: 0 0 10px; line-height: 1.35; }
  .district { margin: 0 0 8px; }
  .district-head, .school-row {
    width: 100%; text-align: left; border: 0; background: transparent; cursor: pointer;
    font: inherit; border-radius: 6px;
  }
  .district-head { padding: 4px 2px; }
  .district-head:hover, .school-row:hover { background: #f3efe6; }
  .school-row { display: block; padding: 2px 6px 2px 18px; font-size: 12px; line-height: 1.35; }
  .school-row.selected { background: #f3e6c8; }
  .district h2 { font-size: 12px; margin: 0; letter-spacing: 0.02em; }
  .district .region { font-size: 11px; color: #6d675e; font-weight: 500; }
  .town { color: #6d675e; }
  .off { opacity: 0.35; }
  .note { font-size: 11px; color: #5c574e; line-height: 1.4; margin-top: 8px; }
  .swatch { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: -1px; border: 1px solid white; box-shadow: 0 0 0 1px rgba(0,0,0,0.25); }
  .leaflet-tooltip.pin-label {
    background: #fffcf8; border: 1px solid #d9d0c2; border-radius: 4px; color: #1c1c1c;
    font-weight: 600; box-shadow: 0 2px 6px rgba(40,30,10,0.12);
  }
</style>
</head>
<body>
<div id="map"></div>
<div id="panel">
  <div class="toolbar">
    <label for="class-select">Class</label>
    <select id="class-select"></select>
  </div>
  <h1 id="title"></h1>
  <p class="sub" id="sub"></p>
  <div id="legend"></div>
  <p class="note">Shading is the geographic span of each district or group’s schools, not an official IHSAA line. Town locations: U.S. Census Bureau 2023 Gazetteer, with campus points where a city has more than one high school. Assignments: IHSAA, March 5, 2025.</p>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const DATA = /*__DATA__*/;
const map = L.map("map", {zoomControl: true});
L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", {
  attribution: "Tiles &copy; Esri",
  maxZoom: 16
}).addTo(map);
const countyLayer = L.geoJSON(DATA.counties, {
  style: {color: "#8a847a", weight: 1, fillColor: "#f7f4ee", fillOpacity: 0.35},
  onEachFeature: (feature, layer) => {
    layer.bindTooltip(feature.properties.name + " County", {sticky: true});
  }
}).addTo(map);
map.fitBounds(countyLayer.getBounds(), {padding: [24, 360]});

const select = document.getElementById("class-select");
DATA.order.forEach(id => {
  const option = document.createElement("option");
  option.value = id;
  option.textContent = DATA.classes[id].label;
  select.appendChild(option);
});

let current = null;
let groups = {};
let visible = {};
let rings = [];
let rowBySchool = {};
let classLayer = L.layerGroup().addTo(map);

function hoverLabel(school) {
  return school.school + " · " + school.town;
}
function esc(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;");
}
function resetMarkers() {
  rings.forEach(ring => map.removeLayer(ring));
  rings = [];
  if (!current) return;
  current.schools.forEach(school => {
    school.marker.setRadius(8);
    school.marker.setStyle({color: "#ffffff", weight: 2, fillColor: school.color, fillOpacity: 1});
    school.marker.unbindTooltip();
    school.marker.bindTooltip(hoverLabel(school), {direction: "top", offset: [0, -8]});
  });
  document.querySelectorAll(".school-row.selected").forEach(row => row.classList.remove("selected"));
}
function showSchool(schoolName, fly) {
  const targets = current.schools.filter(school => school.school === schoolName);
  if (!targets.length) return;
  const district = targets[0].district;
  if (!visible[district]) {
    visible[district] = true;
    classLayer.addLayer(groups[district]);
    rowBySchool[schoolName].closest(".district").classList.remove("off");
  }
  resetMarkers();
  targets.forEach(school => {
    school.marker.setRadius(12);
    school.marker.setStyle({color: "#1a1a1a", weight: 3, fillColor: school.color, fillOpacity: 1});
    school.marker.bringToFront();
    school.marker.unbindTooltip();
    school.marker.bindTooltip(hoverLabel(school), {
      permanent: true,
      direction: "right",
      offset: [14, 0],
      className: "pin-label"
    });
    rings.push(L.circleMarker(school.marker.getLatLng(), {
      radius: 20,
      color: school.color,
      weight: 3,
      fillOpacity: 0,
      interactive: false
    }).addTo(map));
  });
  rowBySchool[schoolName].classList.add("selected");
  targets[0].marker.openPopup();
  if (fly) {
    map.flyToBounds(L.latLngBounds(targets.map(school => school.marker.getLatLng())), {
      paddingTopLeft: [48, 48],
      paddingBottomRight: [400, 48],
      maxZoom: 10,
      duration: 0.55
    });
  }
}
function loadClass(id) {
  const klass = DATA.classes[id];
  if (!klass) return;
  if (current) resetMarkers();
  map.closePopup();
  classLayer.clearLayers();
  current = klass;
  groups = {};
  visible = {};
  rowBySchool = {};
  klass.districts.forEach(d => {
    groups[d] = L.layerGroup().addTo(classLayer);
    visible[d] = true;
  });
  L.geoJSON(klass.zones, {
    style: feature => ({
      color: feature.properties.color,
      weight: 2,
      fillColor: feature.properties.color,
      fillOpacity: 0.28
    }),
    onEachFeature: (feature, layer) => {
      layer.bindTooltip(klass.unit + " " + feature.properties.district + " · " + feature.properties.region);
      groups[feature.properties.district].addLayer(layer);
    }
  });
  klass.schools.forEach(school => {
    const marker = L.circleMarker([school.lat, school.lon], {
      radius: 8,
      color: "#ffffff",
      weight: 2,
      fillColor: school.color,
      fillOpacity: 1
    });
    school.marker = marker;
    const shared = school.shared ? "<br><em>Shared program. Both towns are marked.</em>" : "";
    marker.bindPopup(
      "<strong>" + esc(school.school) + "</strong><br>" +
      esc(school.town) + ", " + esc(school.county) + " County<br>" +
      klass.unit + " " + school.district + " · " + school.region + shared
    );
    marker.bindTooltip(hoverLabel(school), {direction: "top", offset: [0, -8]});
    marker.on("click", () => showSchool(school.school, false));
    groups[school.district].addLayer(marker);
  });
  const bySchool = {};
  klass.schools.forEach(school => {
    (bySchool[school.school] = bySchool[school.school] || []).push(school);
  });
  Object.values(bySchool).forEach(towns => {
    if (towns.length < 2) return;
    const line = L.polyline(towns.map(s => [s.lat, s.lon]), {color: towns[0].color, weight: 2, opacity: 0.9});
    groups[towns[0].district].addLayer(line);
  });

  document.getElementById("title").textContent = klass.label + ", 2025–26";
  document.getElementById("sub").textContent = klass.summary;
  const legend = document.getElementById("legend");
  legend.innerHTML = "";
  const byDistrict = {};
  klass.schools.forEach(school => {
    byDistrict[school.district] = byDistrict[school.district] || [];
    if (!byDistrict[school.district].some(item => item.school === school.school)) byDistrict[school.district].push(school);
  });
  klass.districts.forEach(d => {
    const wrap = document.createElement("div");
    wrap.className = "district";
    const head = document.createElement("button");
    head.className = "district-head";
    head.type = "button";
    const n = byDistrict[d].length;
    head.innerHTML = "<h2><span class='swatch' style='background:" + klass.colors[d] + "'></span>" + klass.unit + " " + d +
      " <span class='region'>· " + klass.regions[d] + " · " + n + "</span></h2>";
    head.addEventListener("click", () => {
      visible[d] = !visible[d];
      if (visible[d]) classLayer.addLayer(groups[d]);
      else classLayer.removeLayer(groups[d]);
      wrap.classList.toggle("off", !visible[d]);
    });
    wrap.appendChild(head);
    const schools = byDistrict[d].slice().sort((a, b) => b.lat - a.lat);
    schools.forEach(school => {
      const row = document.createElement("button");
      row.type = "button";
      row.className = "school-row";
      const towns = bySchool[school.school].map(item => item.town);
      const uniqueTowns = towns.filter((town, index) => towns.indexOf(town) === index);
      row.innerHTML = esc(school.school) + " <span class='town'>" + esc(uniqueTowns.join(" & ")) + "</span>";
      row.addEventListener("click", () => showSchool(school.school, true));
      rowBySchool[school.school] = row;
      wrap.appendChild(row);
    });
    legend.appendChild(wrap);
  });
  select.value = id;
  history.replaceState(null, "", "#" + encodeURIComponent(id));
}
select.addEventListener("change", () => loadClass(select.value));
map.on("click", () => {
  map.closePopup();
  resetMarkers();
});
const fromHash = decodeURIComponent((location.hash || "").replace(/^#/, ""));
loadClass(DATA.classes[fromHash] ? fromHash : "1A");
</script>
</body>
</html>
"""


def parse_args():
    parser = argparse.ArgumentParser(description="Draw IHSAA football district maps.")
    parser.add_argument(
        "classes",
        nargs="*",
        help="Class ids to render (5A 4A 3A 2A 1A A). Default: all.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    places = load_places(DATA / "2023_Gaz_place_national.txt")
    counties = load_counties(DATA / "iowa_counties.geojson")
    selected = args.classes or CLASS_ORDER
    specs = load_class_specs(selected)
    write_site = selected == CLASS_ORDER
    font_name = choose_font()
    print(f"font: {font_name}")
    csv_rows = []
    payloads = []
    for spec in specs:
        records = build_records(spec, places, counties)
        facts = check_records(spec, records, places)
        regions = regions_for(records)
        png, pdf, zones, _state = draw_map(spec, records, counties, regions, font_name)
        payloads.append(class_payload(spec, records, regions, zones))
        for record in records:
            for town in record["towns"]:
                csv_rows.append(
                    [
                        spec["id"],
                        record["district"],
                        spec["unit"],
                        regions[record["district"]],
                        record["school"],
                        town["display"],
                        town["county"],
                        f"{town['lat']:.6f}",
                        f"{town['lon']:.6f}",
                    ]
                )
        print(f"{spec['id']} teams {len(records)} points {sum(len(r['towns']) for r in records)} counts {facts['team_counts']}")
        if spec["id"] == "1A":
            print(f"Eagle Grove is {facts['eagle_miles']:.1f} miles {facts['eagle_direction']} of Clarion, both in {facts['clarion_county']} County")
        print(png)
        print(pdf)
    if write_site:
        csv_path = write_csv(csv_rows)
        html_path = write_html(counties, payloads)
        print(html_path)
        print(csv_path)


if __name__ == "__main__":
    main()
