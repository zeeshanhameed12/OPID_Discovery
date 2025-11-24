# OPID Discovery and Visualization

## Overview

This repository contains code to perform **OPID Discovery** from an OCEL (Object-Centric Event Log) and generate a Petri net-based **OPID (Object Process Interaction Diagram)** model. The discovered model can be visualized with the help of an additional script that handles the visualization. This process involves extracting event logs, dynamically mapping activities to transitions, adding places and arcs to a Petri net, and ultimately exporting the results to a JSON format for further analysis or visualization.

Additionally, a separate script, `view_OPID_Discovery.py`, is provided to help visualize the OPID model once it has been discovered.

## Requirements

Before running the code, ensure that you have the following Python packages installed.

You can install the required dependencies by running:

```bash
pip install pm4py
