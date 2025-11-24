from .transition import Transition
from .opid import OPID

def get_common_transitions(ocpn, object_type1, object_type2, by_label=False):
    """
    Returns the set of transitions common to two object types in the OCPN Petri nets.
    
    Args:
        ocpn: The discovered OCPN dictionary.
        object_type1: The first object type (str).
        object_type2: The second object type (str).
        by_label: If True, compare transitions by label; otherwise, by name.
        
    Returns:
        Set of common transition names or labels.
    """
    net1, _, _ = ocpn["petri_nets"][object_type1]
    net2, _, _ = ocpn["petri_nets"][object_type2]
    if by_label:
        transitions1 = {t.label for t in net1.transitions}
        transitions2 = {t.label for t in net2.transitions}
    else:
        transitions1 = {t.name for t in net1.transitions}
        transitions2 = {t.name for t in net2.transitions}
    a = transitions1.intersection(transitions2)
    return a
def get_transition_name( transition, opid: OPID):
        if transition.label:
            return transition.label
        else:
            if transition in opid.silent_map:
                return opid.silent_map[transition]
            base_name = transition.name if transition.name else "tau"
            silent_name = base_name
            counter = 0
            while silent_name in opid.transition_name_set:
                counter += 1
                silent_name = f"{base_name}_{counter}"
            opid.silent_map[transition] = silent_name
            opid.transition_name_set.add(silent_name)
            opid.add_transition(Transition(silent_name, silent_name, silent=True))
            return silent_name