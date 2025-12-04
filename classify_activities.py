import pm4py
import pandas as pd
import sys
import time
import json
import itertools


MAINTAIN = "MAINTAIN"
CREATE = "CREATE"
DELETE = "DELETE"
UPDATE_PARENT = "UPDATE_PARENT"

Parameters = pm4py.algo.filtering.ocel.activity_type_matching.Parameters

verbose = True

def load_ocel_log(filename):
    """Load the OCEL log from the provided file."""
    return pm4py.read_ocel2_xml(filename) if "xml" in filename \
        else pm4py.read_ocel2_json(filename)

def get_all_events_for_object(o, otype, ocel):
    relations = ocel.relations.drop('ocel:qualifier', axis=1)
    relations = relations[relations["ocel:type"] == otype]
    for row in relations.itertuples():
        if o in row:
          print(row)

def get_events_for_types(ocel, many_type, one_type):
    relations = ocel.relations.drop('ocel:qualifier', axis=1)
    relations_t1 = relations[relations["ocel:type"] == many_type]
    relations_t2 = relations[relations["ocel:type"] == one_type]

    if len(relations_t1) == 0:
        print("no events with %s found" % many_type)
    if len(relations_t2) == 0:
        print("no events with %s found" % one_type)
    
    try:
        reljoin = relations_t1.merge(relations_t2, on="ocel:eid", suffixes=["_t1", "_t2"]) # do the join # , validate="m:1"
    except:
        if verbose:
          print("Relation %s : %s is not many-to-one in log." % (many_type, one_type))
        return None

    # drop some columns, not sure if this is of any help
    reljoin.drop(columns=['ocel:type_t1', 'ocel:type_t2', 'ocel:activity_t2', 'ocel:timestamp_t2'], inplace=True)
    # print("after join:", len(reljoin), len(relations_t1), len(relations_t2))

    is_sorted = reljoin["ocel:timestamp_t1"].is_monotonic_increasing
    assert(is_sorted)
    
    events = {}
    for row in reljoin.itertuples():
        (_, eid, activity, timestamp, many_object, one_object) = row
        if eid not in events:
            events[eid] = {"activity": activity, 
                           "timestamp": timestamp,
                           "one": one_object,
                           "many": set([many_object])
                           }
            if "vh6" in many_object:
                print(events[eid])
        else:
            events[eid]["many"].add(many_object)
    return events

def one_to_one_with(rtype1, rtype2, one2ones):
    oo = any( (t1 == rtype1 and t2 == rtype2) or (t2 == rtype1 and t1 == rtype2) for (t1, t2) in one2ones)
    # print(rtype1, rtype2, oo)
    return oo

def label_activities(events, one_type, relationship_data):
    reference_types = relationship_data["reference types"]
    rel = set([])
    labels = {}

    for eid,data in events.items():
        act = data["activity"]
        one_object = data["one"]
        elabels = set([])
        if reference_types[act] == one_type or \
            one_to_one_with(reference_types[act], one_type, relationship_data["relationships"]["one-to-one"]):
            if one_object == "invoice receipt:2":
                print(data)
            for many_object in data["many"]:
                if (one_object, many_object) in rel:
                    elabels.add(MAINTAIN)
                else:
                    elabels.add(CREATE)
                    if any(o in many_object and u != one_object for (u,o) in rel):
                        print("assumption of implicit deletion violated:", act)
                        print("add", one_object, many_object)
                        print(next( (u,o) for (u,o) in rel if o == many_object and u != one_object ))
                    rel.add((one_object, many_object))
            for o in [ o for (u, o) in rel if u == one_object and o not in data["many"]]:
                rel.remove((one_object, o))
                elabels.add(DELETE)
        else:
            if not (len(data["many"]) == 1):
                print(data)
            assert(len(data["many"]) == 1)
            many_object = list(data["many"])[0]
            if (one_object, many_object) in rel:
                elabels.add(MAINTAIN)
            else:
                parents = [u for (u,o) in rel if o == many_object]
                if len(parents) > 0:
                    if len(parents) != 1:
                        print(data)
                        print(many_object, parents)
                    assert(len(parents) == 1)
                    p = parents[0]
                    rel.remove((p,many_object))
                    rel.add((one_object, many_object))
                    elabels.add(UPDATE_PARENT)
                else:
                    elabels.add(CREATE)
                    rel.add((one_object, many_object))
        
        ltuple = tuple(sorted(list(elabels)))

        # add label for activity
        if not act in labels:
            labels[act] = set([])
        labels[act].add(ltuple)
    # change to list representation
    return dict([ (a, [list(l) for l in ls]) for (a,ls) in labels.items()])

def classify(ocel, relationship_data, many_type, one_type):
    print("-------------------------------------------------------------------")
    print("one-type %s, many-type %s" % (one_type, many_type))

    events = get_events_for_types(ocel, many_type, one_type)

    labels = label_activities(events, one_type, relationship_data)

    print(labels)
    return labels

          
