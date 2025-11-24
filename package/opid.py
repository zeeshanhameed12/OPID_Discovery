
class OPID:
    def __init__(self, name):
        self.name = name
        self.places = []
        self.transitions = []
        self.arcs = []
        self.place_name_map = {}
        self.transition_name_set = set()
        self.silent_map = {}
        self.last_silent_transition = {}
        self.unique_place_id = 0

    def add_place(self, place):
        self.places.append(place)

    def add_transition(self, transition):
        self.transitions.append(transition)
        self.transition_name_set.add(transition)
    
    def add_arc(self, arc):
        self.arcs.append(arc)
    # delete a transition function 
    def delete_transition(self, transition_name):
        self.transitions = [t for t in self.transitions if t.name != transition_name]
        self.transition_name_set.discard(transition_name)
    """def get_transition_name(self, transition):
        if transition.label:
            return transition.label
        else:
            if transition in self.silent_map:
                return self.silent_map[transition]
            base_name = transition.name if transition.name else "tau"
            silent_name = base_name
            counter = 0
            while silent_name in self.transition_name_set:
                counter += 1
                silent_name = f"{base_name}_{counter}"
            self.silent_map[transition] = silent_name
            self.transition_name_set.add(silent_name)
            self.add_transition(Transition(silent_name, silent_name, silent=True))
            return silent_name"""
    def to_json(self):
        return {
            "name": self.name,
            "places": [vars(p) for p in self.places],
            "transitions": [vars(t) for t in self.transitions],
            "arcs": [vars(a) for a in self.arcs],
            "properties": {
                "creator": "PM4Py",
                "source": "OCPN Export",
                "version": "1.0"
            }
        }
