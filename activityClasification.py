import pm4py
import pandas as pd
import time

def load_ocel_log(filename):
    """Load the OCEL log from the provided file."""
    return pm4py.read_ocel2_xml(filename)

def get_activities_and_object_types(ocel):
    """Extract and print the unique activities and object types from the OCEL log."""
    activities = ocel.events["ocel:activity"].unique()
    #print("Activities in OCEL:", activities)
    
    object_types = ocel.relations["ocel:type"].unique()
    print("Please select a pair of object types from the list:", object_types)
    
    return activities, object_types

def get_object_type_pair():
    """Prompt the user to enter two object types for analysis."""
    object_type1 = input("Enter the first object type: ")
    object_type2 = input("Enter the second object type: ")
    return object_type1, object_type2

def process_event_object_relations(ocel):
    """Process the event-to-object relations and store them in a DataFrame."""
    relations = ocel.relations
    relationship_data = []
    
    for _, row in relations.iterrows():
        event_id, activity, object_id, object_type = row["ocel:eid"], row["ocel:activity"], row["ocel:oid"], row["ocel:type"]
        
        event_row = next((entry for entry in relationship_data if entry["event_id"] == event_id), None)
        if event_row is None:
            event_row = {"event_id": event_id, "activity": activity}
            relationship_data.append(event_row)
        
        if object_type not in event_row:
            event_row[object_type] = []
        event_row[object_type].append(object_id)
    
    return pd.DataFrame(relationship_data)

def get_events_for_object_pair(object_id1, object_id2, relations, ocel):
    """Find events and activities involving the given pair of objects."""
    events_with_object1 = relations[relations["ocel:oid"] == object_id1]["ocel:eid"].unique()
    events_with_object2 = relations[relations["ocel:oid"] == object_id2]["ocel:eid"].unique()
    
    common_events = set(events_with_object1).intersection(set(events_with_object2))
    event_activity_list = [(event_id, object_id1, object_id2, ocel.events[ocel.events["ocel:eid"] == event_id]["ocel:activity"].values[0]) 
                           for event_id in common_events]
    
    return event_activity_list


def get_events_for_object_type_pair_via_join(object_type1, object_type2, relations, ocel):
    """Find events and activities involving pairs of objects from two given object types."""
    relations = relations.drop('ocel:qualifier', axis=1)
    relations_t1 = relations[relations["ocel:type"] == object_type1]
    relations_t2 = relations[relations["ocel:type"] == object_type2]
    
    reljoin = relations_t1.merge(relations_t2, on="ocel:eid", suffixes=["_t1", "_t2"]) # do the join

    # drop some columns, not sure if this is of any help
    reljoin.drop(columns=['ocel:type_t1', 'ocel:type_t2', 'ocel:activity_t2', 'ocel:timestamp_t2'], inplace=True)

    result = []
    reljg = reljoin.groupby(by = ["ocel:oid_t1", "ocel:oid_t2"])
    for (object_pair, _) in reljg:
        #print("key", object_pair )
        g = reljg.get_group(object_pair)
        events = []
        for e in g.itertuples(index=False):
          eid = e[0] # event id
          activity = e[1]
          timestamp = e[2]
          events.append((eid, object_pair[0], object_pair[1], activity, timestamp))
        events.sort(key=lambda e: e[4])
        #acts = [ a for _,_,_,a,_ in events ]
        #print(acts)
        result.append(events)
    return result

def get_events_for_object_type_pair(object_type1, object_type2, relations, ocel):
    """Find events and activities involving pairs of objects from two given object types."""
    objects_in_type1 = relations[relations["ocel:type"] == object_type1]["ocel:oid"].unique()
    objects_in_type2 = relations[relations["ocel:type"] == object_type2]["ocel:oid"].unique()

    result = []
    for obj2 in objects_in_type2:
        for obj1 in objects_in_type1:
            events = get_events_for_object_pair(obj1, obj2, relations, ocel)
            if events:
                result.append(events)
    return result

def classify_activities(events_activities):
    """Classify activities based on their position in the event sequence (CREATE, DELETE, MAINTAIN)."""
    activity_labels = {}
    
    for sublist in events_activities:
        if not sublist:
            continue
        
        # Classify first activity in the sublist
        first_activity = sublist[0][3]
        activity_labels.setdefault(first_activity, set()).add("CREATE")
        
        # Classify last activity in the sublist
        last_activity = sublist[-1][3]
        activity_labels.setdefault(last_activity, set()).add("DELETE")
        
        # Classify middle activities in the sublist
        for item in sublist[1:-1]:
            middle_activity = item[3]
            activity_labels.setdefault(middle_activity, set()).add("MAINTAIN")
    
    return activity_labels

def main():
    start_time = time.time()
    
    # Load OCEL log
    #filename = "proceduretopay.xml"
    filename = "post_ocel_inventory_management.xml"
    ocel = load_ocel_log(filename)
    DO_JOIN = True
    
    # Extract activities and object types
    activities, object_types = get_activities_and_object_types(ocel)
    
    # User input for object types to analyze
    object_id1, object_id2 = get_object_type_pair()
    
    # Process event-object relationships
    relationship_df = process_event_object_relations(ocel)
    
    events_activities = None
    # Get events and associated activities for the object type pair
    if DO_JOIN:
        events_activities = get_events_for_object_type_pair_via_join(object_id1, object_id2, ocel.relations, ocel)
    else:
        events_activities = get_events_for_object_type_pair(object_id1, object_id2, ocel.relations, ocel)
        # Sort events chronologically
        for sublist in events_activities:
            sublist.sort(key=lambda x: x[0])
    
    if not events_activities:
        print(f"No common events found involving both objects '{object_id1}' and '{object_id2}'.")
        return  # Stop further processing if no events found

    # Classify activities based on their position in the event sequence
    activity_labels = classify_activities(events_activities)
    
    # Display activity labels
    print("Here is the classification of each activity with labels:")
    for activity, labels in activity_labels.items():
        print(f"Activity: {activity}, Labels: {labels}")
        print("---------------------------------------------------")
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time taken for execution: {execution_time:.2f} seconds")
if __name__ == "__main__":
    main()
