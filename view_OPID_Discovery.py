import json
from graphviz import Digraph
import colorsys

# === Step 1: Load OCPN JSON ===
with open("opid_fi_v1.json", "r") as f:
    ocpn_json = json.load(f)

# === Step 2: Assign consistent colors per object type ===
def get_color_palette(object_types):
    palette = {}
    total = len(object_types)
    for idx, ot in enumerate(sorted(object_types)):
        hue = idx / total
        rgb = colorsys.hsv_to_rgb(hue, 0.6, 0.85)
        hex_color = '#{:02x}{:02x}{:02x}'.format(
            int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255)
        )
        palette[ot] = hex_color
    return palette

# Extract all object types
object_types = set(p["objectType"] for p in ocpn_json["places"])
color_map = get_color_palette(object_types)

# === Step 3: Initialize Graph ===
dot = Digraph("OCPN_Visualization", format="png")
dot.attr(rankdir="LR")  # Left to right layout

# === Step 4: Draw Places ===
for place in ocpn_json["places"]:
    place_name = place["name"]
    obj_type = place["objectType"]
    fillcolor = color_map.get(obj_type, "lightgray")

    # Mark initial/final specially
    if place["initial"]:
        fillcolor = color_map[obj_type]
    elif place["final"]:
        fillcolor = color_map[obj_type]

    dot.node(place_name,
             label="",
             shape="circle",
             style="filled",
             fillcolor=fillcolor)

# === Step 5: Draw Transitions ===
for transition in ocpn_json["transitions"]:
    label = transition["label"] if not transition["silent"] else "τ"
    style = "dashed" if transition["silent"] else "filled"
    dot.node(transition["name"],
             label=label,
             shape="box",
             style=style)

# === Step 6: Draw Arcs with inscriptions and color ===
for arc in ocpn_json["arcs"]:
    source = arc["source"]
    target = arc["target"]
    label = arc.get("inscription", "")
    penwidth = "3" if arc["variable"] else "1"

    # Try to derive object type color from place
    color = "black"
    for place in ocpn_json["places"]:
        if place["name"] == source or place["name"] == target:
            color = color_map.get(place["objectType"], "black")
            break

    # Check if the arc is bidirectional and set direction accordingly
    dir_attr = "both" if arc.get("bidirectional", False) else "forward"

    dot.edge(source, target, label=label, color=color, fontcolor=color, penwidth=penwidth, dir=dir_attr)

# === Step 7: Render and View ===
dot.render("opid_view", view=True)
