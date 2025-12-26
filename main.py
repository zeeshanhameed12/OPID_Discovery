import sys
import time
import json

from classify_activities import load_ocel_log, classify
from OPID_Discovery import discover_opid

# run e.g. as
# python3 main.py input/bicycle_example/log.xml input/bicycle_example/reldata.json
def main():
    start_time = time.time()
    
    # Load OCEL log
    filename = sys.argv[1]
    ocel = load_ocel_log(filename)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time taken for import: {execution_time:.2f} seconds")

    # get reference types
    reftypefile = sys.argv[2]
    with open(reftypefile, "r") as f:
        # load relationship data stored in json 
        relationship_data = json.load(f)
    
        # for now use the first many-to-one relationship mentioned in the relationship data 
        reldata = relationship_data["relationships"]["many-to-one"]
        classification_data = []
        for (many_type, one_type) in reldata:
            activity_classes = classify(ocel, relationship_data, many_type, one_type)
            classification_data.append((many_type, one_type, activity_classes))
        
        discover_opid(ocel, classification_data)
        print("Please run view_OPID_Discovery.py to visualize the generated OPID.")

    
    # Calculate execution time
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Time taken for execution: {execution_time:.2f} seconds")

if __name__ == "__main__":
    main()