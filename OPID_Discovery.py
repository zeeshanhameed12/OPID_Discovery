import pm4py
import json
import uuid
import re
from pm4py.algo.discovery.ocel.ocpn.variants import classic as ocpn_discovery
from pm4py.objects.petri_net.obj import PetriNet
from package import Place, Transition, Arc, OPID, get_transition_name

# Load OCEL log
filename = "selfocel.xml"
classification_activity = {
    "collect": [["CREATE"]],
    "assemble_w": [["MAINTAIN"], ["UPDATE_PARENT"]],
    "assemble_h": [["MAINTAIN"], ["DELETE"]],
}

# Read OCEL log
ocel = pm4py.read_ocel2_xml(filename)
print(f"The object types in the OCEL are: {pm4py.ocel.ocel_get_object_types(ocel)}")

# Get object type pair from user input
object_type_pair = input("Enter the object type pairs in the format (objectType1, objectType2), separated by commas: ")

# Validate input format
"""if len(object_type_pair) != 2:
    print(f"Invalid pair: {object_type_pair}. Expected format is (objectType1, objectType2).")
    exit(1)"""

# Parse the input string into a tuple
object_type_pair = tuple(map(str.strip, re.findall(r'\(([^,]+),([^)]+)\)', object_type_pair)[0]))
print("Please run view_OPID_Discovery.py file to visualize the generated OPID for the object type pair:", object_type_pair)

# Initialize OPID and OCPN discovery
ocpn = ocpn_discovery.apply(ocel)
opid = OPID("Self OCPN Export")

# Add transitions from discovered OCPN
for act in ocpn["activities"]:
    opid.add_transition(Transition(name=act, label=act, silent=False))

# Add places and arcs for each Petri Net
for ot, (net, initial_marking, final_marking) in ocpn["petri_nets"].items():
    # Add places to OPID
    for place in net.places:
        place_name = f"place_{opid.unique_place_id}"
        opid.place_name_map[place] = place_name
        opid.unique_place_id += 1
        opid.add_place(Place(
            name=opid.place_name_map[place],
            objectType=ot,
            initial=place in initial_marking,
            final=place in final_marking
        ))

    # Add arcs to OPID
    for arc in net.arcs:
        if arc.source in opid.place_name_map:
            source_name = opid.place_name_map[arc.source]
            target_name = get_transition_name(arc.target, opid)
        else:
            source_name = get_transition_name(arc.source, opid)
            target_name = opid.place_name_map[arc.target]
        
        is_double = (
            arc.target.label in ocpn["double_arcs_on_activity"][ot]
            and ocpn["double_arcs_on_activity"][ot][arc.target.label]
        ) if isinstance(arc.source, PetriNet.Place) else (
            arc.source.label in ocpn["double_arcs_on_activity"][ot]
            and ocpn["double_arcs_on_activity"][ot][arc.source.label]
        )

        penwidth = "4.0" if is_double else "1.0"
        opid.add_arc(Arc(
            source=source_name,
            target=target_name,
            weight=penwidth,
            variable=is_double,
            inscription=ot[0].capitalize() if is_double else ot[0],
        ))

    # Add silent transitions and arcs
    for place in final_marking:
        silent_name = f"tau_end_{ot}_{uuid.uuid4()}"
        opid.add_transition(Transition(name=silent_name, label="", silent=True))
        opid.last_silent_transition[ot] = silent_name
        opid.add_arc(Arc(
            source=opid.place_name_map[place],
            target=silent_name,
            inscription=ot[0]
        ))

    for place in initial_marking:
        silent_name = f"tau_start_{ot}_{uuid.uuid4()}"
        opid.add_transition(Transition(name=silent_name, label="", silent=True))
        opid.add_arc(Arc(
            source=silent_name,
            target=opid.place_name_map[place],
            inscription=f"v_{ot[0]}"
        ))

# Create pL1 for stable relations
pL1 = Place(f"{object_type_pair}", objectType=f"{object_type_pair}")
opid.add_place(pL1)

# Add transitions for each classification in classification_activity
for activity, classifications in classification_activity.items():
    original_activity_label = activity
    activity_label = f"{activity}_{'_'.join(classifications[0])}"

    # Update the activity label in OPID transitions
    for t in opid.transitions:
        if t.name == original_activity_label:
            t.label = activity_label

    # Create copies of the activity for multiple classifications
    for i in range(1, len(classifications)):
        activity_copy = f"{activity}_{'_'.join(classifications[i])}"
        opid.add_transition(Transition(name=activity_copy, label=activity_copy, silent=False))

        # Copy the arcs to and from the original activity to the new activity_copy
        for arc in opid.arcs:
            if arc.source == original_activity_label:
                opid.add_arc(Arc(
                    source=activity_copy,
                    target=arc.target,
                    weight=arc.weight,
                    variable=arc.variable,
                    inscription=arc.inscription
                ))
            if arc.target == original_activity_label:
                opid.add_arc(Arc(
                    source=arc.source,
                    target=activity_copy,
                    weight=arc.weight,
                    variable=arc.variable,
                    inscription=arc.inscription
                ))

# Add arcs based on transition labels
for t in opid.transitions:
    if not t.silent:
        label = t.label
        if "CREATE" in label:
            opid.add_arc(Arc(
                source=t.name,
                target=pL1.name,
                weight=True,
                variable=True,
                inscription=f"Create_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
            ))
        elif "DELETE" in label:
            opid.add_arc(Arc(
                source=pL1.name,
                target=t.name,
                weight=True,
                variable=True,
                inscription=f"Delete_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
            ))
        elif "MAINTAIN" in label:
            opid.add_arc(Arc(
                source=t.name,
                target=pL1.name,
                weight=True,
                variable=True,
                inscription=f"Maintain_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})",
                bidirectional=True
            ))
        elif "UPDATE_PARENT" in label:
            # Update parent logic with arcs
            for arc in opid.arcs:
                if arc.target == t.name and arc.variable:
                    source_place = arc.source
                elif arc.source == t.name and arc.variable:
                    target_place = arc.target

            opid.add_arc(Arc(
                source=source_place,
                target=t.name,
                weight=False,
                variable=False,
                inscription=f"update_parent_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
            ))
            opid.add_arc(Arc(
                source=t.name,
                target=target_place,
                weight=False,
                variable=False,
                inscription=f"update_parent_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
            ))
            opid.add_arc(Arc(
                source=t.name,
                target=pL1.name,
                weight=False,
                variable=False,
                inscription=f"update_parent_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})",
                bidirectional=False
            ))
            opid.add_arc(Arc(
                source=pL1.name,
                target=t.name,
                weight=False,
                variable=False,
                inscription=f"update_parent_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})",
                bidirectional=False
            ))

# Output to JSON
output_path = "opid_fi_v1.json"
with open(output_path, 'w') as json_file:
    json.dump(opid.to_json(), json_file, indent=4)
