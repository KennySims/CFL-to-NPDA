from collections import defaultdict, deque

def CFG_to_NPDA(cfg):
    initialState = cfg.split("->")[0].strip()  # Get the initial state from the first production
    productions = defaultdict(list)
    for line in cfg.splitlines():
            left, right = line.split("->")
            left = left.strip()
            for rule in right.split("|"):
                productions[left].append(rule.strip())
    # Create NPDA components
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
    Transformed_NPDA += ("-b-b-empty->p2,q2-empty-z-z->q3")
    maxState = 3
    for nonTerminal in productions:
        for rule in productions[nonTerminal]:
            currentState = 3
            if len(rule) > 1 and rule != "empty" and not (len(rule) == 2 and str(rule[1]) == str(nonTerminal)):
                # Start transition: replace nonTerminal with last character of rule
                maxState += 1
                Transformed_NPDA += (",q2-empty-" + nonTerminal + "-" + str(rule[-1]) + "->q" + str(maxState))
                currentState = maxState
                
                # Process each character in reverse order (from second-to-last to first)
                for i in range(len(rule)-2, -1, -1):
                    if i == 0:
                        # Last transition: return to q2
                        Transformed_NPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q2")
                    else:
                        # Intermediate transitions: replace character with next_char + character
                        maxState += 1
                        next_char = rule[i-1]
                        Transformed_NPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q" + str(maxState))
                        currentState = maxState
    if maxState > 3:
        for i in range(maxState - 3):
            Transformed_NPDA = ",q" + str(maxState - i) + Transformed_NPDA
    Transformed_NPDA = "q1,q2,q3f" + Transformed_NPDA

    return Transformed_NPDA

def Run_NPDA(npda, string):
    """
    Run NPDA simulation on input string
    Format: states,transitions where states ending with 'f' are accepting
    Transitions: state-input-stack_top-new_stack->next_state
    Returns 'accept' or 'reject'
    """
    # Parse the NPDA
    parts = npda.split(',')
    starting_state = parts[0]  # First state is the starting state
    
    # Find where transitions start (after the states)
    states_end = 0
    for i, part in enumerate(parts):
        if '->' in part:
            states_end = i
            break
    
    # Extract states and accepting states
    states = []
    accepting_states = set()
    
    for i in range(states_end):
        state = parts[i]
        if state.endswith('f'):
            clean_state = state[:-1]  # Remove 'f'
            states.append(clean_state)
            accepting_states.add(clean_state)
        else:
            states.append(state)
    
    # Parse transitions
    transitions = defaultdict(list)
    
    # Reconstruct transition string from remaining parts
    transition_parts = parts[states_end:]
    transition_str = ','.join(transition_parts)
    
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
                
                transitions[state].append({
                    'input': input_sym,
                    'stack_top': stack_top,
                    'new_stack': new_stack,
                    'next_state': right
                })
    #print(transitions)  # Debug: print parsed transitions
    
    # BFS simulation with threads
    # Each thread: (state, remaining_input, stack, depth)
    queue = deque([(starting_state, string, ['z'], 0)])  # Start with initial state, full string, stack with bottom marker
    
    while queue:
        current_state, remaining_input, stack, depth = queue.popleft()
        
        # Check depth limit
        if depth >= 50:
            continue
            
        # Check if we can accept (in accepting state, no more input)
        # Allow acceptance with any stack configuration, not just empty stack
        if (current_state in accepting_states and not remaining_input and not stack):
            return 'accept'
        # Try all possible transitions from current state
        if current_state in transitions:
            for transition in transitions[current_state]:
                input_sym = transition['input']
                stack_top = transition['stack_top']
                new_stack_sym = transition['new_stack']
                next_state = transition['next_state']
                
                # Check if transition is applicable
                can_apply = False
                new_remaining_input = remaining_input
                new_stack = stack.copy()
                
                # Handle input consumption
                if input_sym == '':  # Epsilon transition
                    can_apply = True
                elif remaining_input and remaining_input[0] == input_sym:
                    new_remaining_input = remaining_input[1:]
                    can_apply = True
                else:
                    continue  # Can't apply this transition
                
                # Handle stack operations
                if stack_top == '':  # No stack requirement
                    # Just push new symbols if any
                    if new_stack_sym:
                        # Push in reverse order since stack is LIFO
                        for sym in reversed(new_stack_sym):
                            new_stack.append(sym)
                elif stack and stack[-1] == stack_top:
                    # Pop the required symbol
                    new_stack.pop()
                    # Push new symbols if any
                    if new_stack_sym:
                        for sym in reversed(new_stack_sym):
                            new_stack.append(sym)
                elif not stack and stack_top == 'z':
                    # Special case: trying to match bottom marker when stack is empty
                    continue
                else:
                    continue  # Can't apply transition
                
                if can_apply:
                    queue.append((next_state, new_remaining_input, new_stack, depth + 1))
    
    return 'reject'
    
#def Intersection_NPDA_NFA(npda, nfa):
#    return Intersection

# Example CFG input
example_cfg = """S -> XaXaX
X -> aXb|bXa|XX|empty"""

print("CFG input:")
print(example_cfg)
print("\nCFG output:")
npda_result = CFG_to_NPDA(example_cfg)
print(npda_result)

# Test the NPDA with some strings
print("\n--- Testing NPDA ---")
test_strings = ["aaba", "abab", "aa", "abba", "aabaa"]
for test_str in test_strings:
    result = Run_NPDA(npda_result, test_str)
    print(f"String '{test_str}': {result}")
