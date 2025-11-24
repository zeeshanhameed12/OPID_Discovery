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
"collect": [ ["CREATE"] ],
"assemble_w": [ ["MAINTAIN"],["UPDATE_PARENT"] ],
"assemble_h": [ ["MAINTAIN"], ["DELETE"] ],

}
#filename = "ContainerLogistics.xml"
ocel = pm4py.read_ocel2_xml(filename)
print(f"The object types in the OCEL are: {pm4py.ocel.ocel_get_object_types(ocel)}")
object_type_pair = input("Enter the object tyope pairs in the format (objectType1, objectType2), separated by commas: ")
"""if len(object_type_pair) != 2:
        print(f"Invalid pair: {object_type_pair}. Expected format is (objectType1, objectType2).")
        exit(1)"""
# parse the input string into a tuple as it is only one pair
object_type_pair = tuple(map(str.strip, re.findall(r'\(([^,]+),([^)]+)\)', object_type_pair)[0]))

print("Input string:", object_type_pair)



# Initialize OPID and OCPN discovery
ocpn = ocpn_discovery.apply(ocel)
opid = OPID("Self OCPN Export")

# Add transitions from discovered OCPN
for act in ocpn["activities"]:
    opid.add_transition(Transition(name=act, label=act, silent=False))

# Places and Arcs for each Petri Net
for ot, (net, initial_marking, final_marking) in ocpn["petri_nets"].items():
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

    for arc in net.arcs:
        if arc.source in opid.place_name_map:
            source_name = opid.place_name_map[arc.source]
            target_name = get_transition_name(arc.target, opid)
        else:
            source_name = get_transition_name(arc.source, opid)
            target_name = opid.place_name_map[arc.target]
        if type(arc.source) is PetriNet.Place:
            is_double = (
                arc.target.label in ocpn["double_arcs_on_activity"][ot]
                and ocpn["double_arcs_on_activity"][ot][arc.target.label]
            )
            penwidth = "4.0" if is_double else "1.0"
        elif type(arc.source) is PetriNet.Transition:
            is_double = (
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
        # loof through cllaasification_activity. if activity have multiple lists, creadte a copy of that activity and add it the transitions using opid.add_transition
    
for activity, classifications in classification_activity.items():
        # update the label of the activity by concatinatinthe first element of each classification list with underscores
        # for example "collect": [ ["CREATE"], ["CREATE", "SINGLETON"] ], becomes "collect_CREATE"
        original_activity_label = activity
        activity_label = f"{activity}_{'_'.join(classifications[0])}"
           # update the activity in opid transitions
        for t in opid.transitions:
            if t.name == original_activity_label:
                t.label = activity_label
        # now if there are multiple classifications for the activity, create copies of the activity and corresponding arcs
        for i in range(1, len(classifications)):
            activity_copy = f"{activity}_{'_'.join(classifications[i])}"
            opid.add_transition(Transition(name=activity_copy, label=activity_copy, silent=False))

            # also copy the arcs to and from the origional activity to the new activity_copy
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
# iterate throgh all transition except silent transitions
for t in opid.transitions:
    if not t.silent:
        label=t.label
        if "CREATE" in label:
            opid.add_arc(Arc(
                    source=t.name,
                    target=pL1.name,
                    weight=is_double,
                    variable=True,
                    inscription=f"Create_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
                ))
        if "DELETE" in label:
            opid.add_arc(Arc(
                    source=pL1.name,
                    target=t.name,
                    weight=is_double,
                    variable=True,
                    inscription=f"Delete_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})"
                ))
        if "MAINTAIN" in label:
            opid.add_arc(Arc(
                    source=t.name,
                    target=pL1.name,
                    weight=is_double,
                    variable=True,
                    inscription=f"Maintain_({object_type_pair[0][0].capitalize()},{object_type_pair[1][0]})",
                    bidirectional=True
                ))
        if "UPDATE_PARENT" in label:
            # for UPDATE_PARENT, we we do the following
            # 1. Get all incoming arcs of this transition and find the arc with parameter weight = is_double
            for arc in opid.arcs:
                if arc.target == t.name:
                    # get source the arc whci has parameter variable = True and also weight = is_double
                    if arc.variable:
                        source_place = arc.source
                if arc.source == t.name:
                    if arc.variable:
                        target_place = arc.target 

           # print(f"Source place for UPDATE_PARENT arc: {source_place}")
                    # create an arc from source_place to transition t with inscription object type
            opid.add_arc(Arc(
                    source=source_place,
                    target=t.name,
                    weight=False,
                    variable=False,
                    # the inscription should be update_parent_(objectType1,objectType2) with brackets
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
        #print(f"Transition: {t.name}, Label: {t.label}")
# Output to JSON
output_path = "opid_fi_v1.json"
with open(output_path, 'w') as json_file:
    json.dump(opid.to_json(), json_file, indent=4)
