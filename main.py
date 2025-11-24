import sys
import time
import json

from classify_activities import load_ocel_log, classify
from OPID_Discovery import discover_opid

# run e.g. as
# python classify_activities.py input/ocel/proceduretopay.xml input/metadata/proceduretopay.json "goods receipt" payment
# python classify_activities.py input/ocel/selfocel.xml input/metadata/selfocel.json wheel frame
def main():
    start_time = time.time()
    
    # Load OCEL log
    filename = sys.argv[1]
    ocel = load_ocel_log(filename)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time taken for import: {execution_time:.2f} seconds")

    # get_all_events_for_object("vh6", "Vehicle", ocel)

    # get reference types
    reftypefile = sys.argv[2]
    with open(reftypefile, "r") as f:
        relationship_data = json.load(f)
    
        (many_type, one_type) = relationship_data["relationships"]["many-to-one"][0]
        activity_classes = classify(ocel, relationship_data, many_type, one_type)
        discover_opid(ocel, (many_type, one_type), activity_classes)
            
    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time taken for execution: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()