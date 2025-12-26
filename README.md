# Object-Centric Processes with Dynamic Relationships

## Overview

This repository contains supporting material for the paper *Discovering the Lively World of Object-Centric Processes with Dynamic Relationships* by Alessandro Gianola, Zeeshan Hameed, Marco Montali, Anjo Seidel, Mathias Weske, and Sarah Winkler, see `paper.pdf` for an extended version.

Especially, the repository contains code to perform **OPID Discovery** from an OCEL (Object-Centric Event Log) and generate a Petri net-based **OPID (Object Process Interaction Diagram)** model. The discovered model can be visualized with the help of an additional script that handles the visualization. This process involves extracting event logs, dynamically mapping activities to transitions, adding places and arcs to a Petri net, and ultimately exporting the results to a JSON format for further analysis or visualization.

## Requirements

Before running the code, ensure that you have the following Python packages installed.

You can install the required dependencies by running:

```bash
pip install pm4py
```

## Running the tool

The entry point of the tool is `main.py`, which takes two arguments:

 - The first one must be the path of an OCEL in `jsonocel` or `xml` format.
 - The second argument must be the path of a `json` file that contains respective relationship data.

Example calls are as follows:
```
python3 main.py examples/bicycle_example/log.xml examples/bicycle_example/reldata.json
python3 main.py examples/paper_example/log.jsonocel examples/paper_example/reldata.json
```
These calls produce an OPID in json format, stored in the file `transformed_opid.json`.
To view the OPID, run
```
python3 view_OPID_Discovery.py
```
which produces a dot file and a picture `opid_view.png`.


