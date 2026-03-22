from collections import defaultdict, deque

def CFG_to_NPDA(cfg):
    initialState = cfg.split("->")[0].strip() 
    productions = defaultdict(list)
    for line in cfg.splitlines():
            left, right = line.split("->")
            left = left.strip()
            for rule in right.split("|"):
                productions[left].append(rule.strip())
    Transformed_NPDA = ""
    Transformed_NPDA += (",q1-empty-z-" + str(initialState) + "z->q2")

    maxState = 1
    loopCounter = 0
    for nonTerminal in productions:
        for rule in productions[nonTerminal]:
            if len(rule) == 1 or rule == "empty" or len(rule) == 2 and str(rule[1]) == str(nonTerminal):
                if loopCounter == 0:
                    Transformed_NPDA += (",q2")
                loopCounter += 1
        for rule in productions[nonTerminal]:
            if len(rule) == 1 or rule == "empty" or len(rule) == 2 and str(rule[1]) == str(nonTerminal):
                if loopCounter != 0:
                    Transformed_NPDA += ("-empty-" + nonTerminal + "-" + str(rule) + "|")      
                else:
                    Transformed_NPDA += ("-empty-" + nonTerminal + "-" + str(rule) + "->q2")
    Transformed_NPDA += ("-a-a-empty|")
    Transformed_NPDA += ("-b-b-empty->q2,q2-empty-z-z->q3")
    maxState = 3
    for nonTerminal in productions:
        for rule in productions[nonTerminal]:
            currentState = 3
            if len(rule) > 1 and rule != "empty" and not (len(rule) == 2 and str(rule[1]) == str(nonTerminal)):
                maxState += 1
                Transformed_NPDA += (",q2-empty-" + nonTerminal + "-" + str(rule[-1]) + "->q" + str(maxState))
                currentState = maxState
                
                for i in range(len(rule)-2, -1, -1):
                    if i == 0:
                        Transformed_NPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q2")
                    else:
                        maxState += 1
                        Transformed_NPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q" + str(maxState))
                        currentState = maxState
    if maxState > 3:
        for i in range(maxState - 3):
            Transformed_NPDA = ",q" + str(maxState - i) + Transformed_NPDA
    Transformed_NPDA = "q1,q2,q3f" + Transformed_NPDA

    return Transformed_NPDA

def Run_NPDA(npda, string):
    parts = npda.split(',')
    starting_state = parts[0] 
    
    # Find where transitions start (after the states)
    states_end = 0
    for i, part in enumerate(parts):
        if '->' in part:
            states_end = i
            break
    
    # Extract accepting states only (optimization: don't store all states)
    accepting_states = set()
    
    for i in range(states_end):
        state = parts[i]
        if state.endswith('f'):
            clean_state = state[:-1]  # Remove 'f'
            accepting_states.add(clean_state)
    
    # Parse transitions with optimized storage
    transitions = defaultdict(list)
    
    # Reconstruct transition string from remaining parts
    transition_parts = parts[states_end:]
    
    # Split transitions by commas but be careful of transitions that span multiple parts
    trans_list = []
    current_trans = ""
    
    for part in transition_parts:
        if current_trans:
            current_trans += "," + part
        else:
            current_trans = part
            
        if '->' in current_trans:
            trans_list.append(current_trans)
            current_trans = ""
    
    # Parse each transition
    for trans in trans_list:
        if '->' not in trans:
            continue
            
        left, right = trans.split('->')
        right = right.strip()
        
        # Handle multiple source transitions separated by |
        if '|' in left:
            source_transitions = left.split('|')
            # Get the state from the first transition
            first_trans_parts = source_transitions[0].strip().split('-')
            if len(first_trans_parts) >= 1:
                base_state = first_trans_parts[0]
            else:
                continue
                
            # Reconstruct full transitions for subsequent parts
            reconstructed_transitions = []
            for i, source_trans in enumerate(source_transitions):
                source_trans = source_trans.strip()
                if not source_trans:
                    continue
                    
                if i == 0:
                    # First transition is complete
                    reconstructed_transitions.append(source_trans)
                else:
                    # Subsequent transitions need state prefixed
                    if source_trans.startswith('-'):
                        reconstructed_transitions.append(base_state + source_trans)
                    else:
                        reconstructed_transitions.append(source_trans)
        else:
            reconstructed_transitions = [left.strip()]
            
        for source_trans in reconstructed_transitions:
            source_trans = source_trans.strip()
            if not source_trans:
                continue
                
            parts_trans = source_trans.split('-')
            if len(parts_trans) >= 4:
                state = parts_trans[0]
                input_sym = parts_trans[1] if parts_trans[1] != 'empty' else ''
                stack_top = parts_trans[2] if parts_trans[2] != 'empty' else ''
                new_stack = '-'.join(parts_trans[3:]) if parts_trans[3] != 'empty' else ''
                
                transitions[state].append({ 'input': input_sym, 'stack_top': stack_top, 'new_stack': new_stack, 'next_state': right })
    
    string_len = len(string)
    queue = deque([(starting_state, 0, ('z',), 0)])
    
    # Memoization: track visited configurations to avoid redundant exploration
    visited = set()
    
    while queue:
        current_state, input_pos, stack_tuple, depth = queue.popleft()
        #print(f"Current state: {current_state}, Input position: {input_pos}, Stack: {stack_tuple}, Depth: {depth}")
        
        # Early termination conditions
        if depth >= 50:  # Depth limit to prevent infinite loops
            continue
        # Create configuration key for memoization
        config_key = (current_state, input_pos, stack_tuple)
        if config_key in visited:
            #print(f"Already visited: {config_key}, skipping...")
            continue
        visited.add(config_key)
        
        # Check acceptance condition - modified based on NPDA semantics
        if (current_state in accepting_states and input_pos == string_len):
            return 'accept'
        
        # Try all possible transitions from current state
        if current_state in transitions:
            for transition in transitions[current_state]:
                input_sym = transition['input']
                stack_top = transition['stack_top']
                new_stack_sym = transition['new_stack']
                next_state = transition['next_state']
                
                # Check input consumption
                can_apply = False
                new_input_pos = input_pos
                
                if input_sym == '':  # Epsilon transition
                    can_apply = True
                elif input_pos < string_len and string[input_pos] == input_sym:
                    new_input_pos = input_pos + 1
                    can_apply = True
                else:
                    continue
                
                # Check stack operations
                stack_list = list(stack_tuple)
                
                if stack_top == '':  # No stack requirement
                    # Just push new symbols if any
                    if new_stack_sym:
                        # Push in reverse order since stack is LIFO
                        for sym in reversed(new_stack_sym):
                            stack_list.append(sym)
                elif stack_list and stack_list[-1] == stack_top:
                    # Pop the required symbol
                    stack_list.pop()
                    # Push new symbols if any
                    if new_stack_sym:
                        for sym in reversed(new_stack_sym):
                            stack_list.append(sym)
                elif not stack_list and stack_top == 'z':
                    # Special case: trying to match bottom marker when stack is empty
                    continue
                else:
                    continue  # Can't apply transition
                
                if can_apply:
                    new_stack_tuple = tuple(stack_list)
                    new_config = (next_state, new_input_pos, new_stack_tuple)
                
                    # Only add if not already visited (additional check for efficiency)
                    if new_config not in visited and len(new_stack_tuple) < 15:
                        queue.append((next_state, new_input_pos, new_stack_tuple, depth + 1))
    
    return 'reject'
    
def parse_automaton_to_dict(automaton_string, automaton_type):
    
    # Split into states and transitions
    parts = automaton_string.split(',')
    states_string = parts[0]
    
    # Parse states from concatenated format
    def parse_states_from_string(states_str):
        states = []
        accept_states = set()
        i = 0
        current_state = ""
        
        while i < len(states_str):
            char = states_str[i]
            
            if char.isalpha() and char.islower() and current_state == "":
                # Start of new state (like 'q' or 'r')
                current_state += char
            elif char.isdigit():
                # Part of state name
                current_state += char
            elif char == 'f':
                # Accept state marker
                if current_state:
                    states.append(current_state + 'f')
                    accept_states.add(current_state)
                    current_state = ""
            elif char.isalpha() and char.islower() and current_state != "":
                # Start of next state
                if current_state:
                    states.append(current_state)
                current_state = char
            
            i += 1
        
        # Add final state if exists
        if current_state:
            states.append(current_state)
        
        return states, accept_states
    
    states, accept_states = parse_states_from_string(states_string)
    
    # Parse transitions
    transitions = {}
    transition_list = []
    
    for i in range(1, len(parts)):
        trans_part = parts[i]
        if '->' in trans_part:
            left, right = trans_part.split('->')
            right = right.strip()
            
            if automaton_type == "NPDA":
                # Handle NPDA transitions with stack operations
                if '|' in left:
                    # Multiple stack operations
                    operations = left.split('|')
                    base_state = None
                    base_input = None
                    
                    for j, op in enumerate(operations):
                        op = op.strip()
                        op_parts = op.split('-')
                        
                        if j == 0:
                            # First operation has state
                            if len(op_parts) >= 4:
                                base_state = op_parts[0]
                                base_input = op_parts[1] if op_parts[1] != 'empty' else ''
                                stack_top = op_parts[2]
                                stack_push = op_parts[3]
                                
                                transition_info = {'from_state': base_state, 'input': base_input, 'stack_top': stack_top, 'stack_push': stack_push, 'to_state': right
                                }
                                transition_list.append(transition_info)
                        else:
                            # Subsequent operations
                            if len(op_parts) >= 3:
                                input_sym = op_parts[0] if op_parts[0] != 'empty' else ''
                                stack_top = op_parts[1]
                                stack_push = op_parts[2]
                                
                                # Process all operations regardless of input symbol
                                transition_info = {'from_state': base_state,'input': input_sym,'stack_top': stack_top,'stack_push': stack_push,'to_state': right
                                }
                                transition_list.append(transition_info)
                else:
                    # Single operation
                    op_parts = left.strip().split('-')
                    if len(op_parts) >= 4:
                        from_state = op_parts[0]
                        input_sym = op_parts[1] if op_parts[1] != 'empty' else ''
                        stack_top = op_parts[2]
                        stack_push = op_parts[3]
                        
                        transition_info = {'from_state': from_state,'input': input_sym,'stack_top': stack_top,'stack_push': stack_push,'to_state': right
                        }
                        transition_list.append(transition_info)
            else:
                # NFA transitions with support for "or" syntax (a|b)
                left_parts = left.split('-')
                if len(left_parts) >= 2:
                    from_state = left_parts[0]
                    input_sym = left_parts[1]
                    
                    # Handle multiple inputs separated by |
                    if '|' in input_sym:
                        # Split by | and create separate transitions for each input
                        input_options = input_sym.split('|')
                        for input_option in input_options:
                            input_option = input_option.strip()
                            transition_info = {'from_state': from_state,'input': input_option,'to_state': right
                            }
                            transition_list.append(transition_info)
                    else:
                        # Single input transition
                        transition_info = {'from_state': from_state,'input': input_sym,'to_state': right
                        }
                        transition_list.append(transition_info)
    
    # Group transitions by source state
    for trans in transition_list:
        from_state = trans['from_state']
        if from_state not in transitions:
            transitions[from_state] = []
        transitions[from_state].append(trans)
    
    # Build the result dictionary
    result = {
        'states': states,
        'accepting_states': accept_states,
        'transitions': transitions,
    }
    
    return result

def Intersection_NPDA_NFA(npda, nfa):
    final_npda = ""
    npda_dict = parse_automaton_to_dict(npda, "NPDA")
    nfa_dict = parse_automaton_to_dict(nfa, "NFA")
    
    npda_states = npda_dict['states']
    npda_transitions = npda_dict['transitions']
    
    nfa_states = nfa_dict['states']
    nfa_transitions = nfa_dict['transitions']
    for npda_state in npda_states:
        for nfa_state in nfa_states:
            if npda_state.endswith('f') and nfa_state.endswith('f'):
                final_npda += nfa_state[:-1] + npda_state + ','
            elif nfa_state.endswith('f'):
                final_npda += nfa_state[:-1] + npda_state + ','
            elif npda_state.endswith('f'):
                final_npda += nfa_state + npda_state[:-1] + ','
            else:
                final_npda += nfa_state + npda_state + ','
    for npda_state_name in npda_transitions:
        for nfa_state_name in nfa_transitions:
            for npda_trans in npda_transitions[npda_state_name]:
                for nfa_trans in nfa_transitions[nfa_state_name]:
                    if npda_trans['input'] == nfa_trans['input']:
                        final_npda += nfa_trans['from_state'] + npda_trans['from_state'] + '-' + npda_trans['input'] + '-' + npda_trans['stack_top'] + '-' + npda_trans['stack_push'] + '->' + nfa_trans['to_state'] + npda_trans['to_state'] + ','
                    if npda_trans['input'] == '':
                        final_npda += nfa_trans['from_state'] + npda_trans['from_state'] + '-empty-' + npda_trans['stack_top'] + '-' + npda_trans['stack_push'] + '->' + nfa_trans['to_state'] + npda_trans['to_state'] + ','
    final_npda = final_npda[:-1] 
    return final_npda 

#Example CFG input
example_cfg = """S -> U|V
U -> XAX|UU
V -> XBX|VV
X -> aXb|bXa|XX|empty
A -> aA|a
B -> bB|b"""

print("CFG input:")
print(example_cfg)
print("\nCFG output:")
npda_result = CFG_to_NPDA(example_cfg)
print(npda_result)

# Test the NPDA with some strings
print("\n--- Testing NPDA ---")
test_strings = ["bbbaab", "aababb"]
for test_str in test_strings:
    result = Run_NPDA(npda_result, test_str)
    print(f"String '{test_str}': {result}")

# Test NPDA-NFA Intersection
print("\n--- Testing NPDA-NFA Intersection ---")
example_nfa = "q1fq2fq3fq4,q1-a->q1,q1-b->q2,q2-a->q2,q2-b->q3,q3-a->q3,q3-b->q4,q4-a|b->q4"
example_npda = "q1q2q3q4fq5,q1-empty-z-az->q2,q2-empty-a-aa->q3,q3-empty-a-aa->q4,q4-a-a-empty|b-z-z|b-a-a->q4"
test = Intersection_NPDA_NFA(example_npda, example_nfa)
print("\n--- Testing NPDA ---")
test_strings = ["baaba", "baaaab"]
for test_str in test_strings:
    result = Run_NPDA(test, test_str)
    print(f"String '{test_str}': {result}")
