from collections import defaultdict, deque

# ---------------------------
# Step 1: Parse CFG
# ---------------------------
def parse_cfg(lines):
    cfg = {}
    for line in lines:
        left, right = line.split("->")
        left = left.strip()
        productions = right.strip().split("|")

        cfg[left] = []
        for prod in productions:
            prod = prod.strip()
            if prod == "empty":
                cfg[left].append([])
            else:
                # Better parsing: split by spaces if present, otherwise individual chars
                if " " in prod:
                    cfg[left].append(prod.split())
                else:
                    cfg[left].append(list(prod))
    return cfg


# ---------------------------
# Step 2: Build NPDA
# ---------------------------
def build_npda(cfg):
    transitions = defaultdict(list)
    
    # Find all terminals in the grammar
    terminals = set()
    variables = set(cfg.keys())
    
    for var in cfg:
        for production in cfg[var]:
            for symbol in production:
                if symbol not in variables and symbol != "":
                    terminals.add(symbol)

    start_symbol = list(cfg.keys())[0]

    # Start transition
    transitions[("q0", "", "z")].append(("q1", [start_symbol, "z"]))

    # Variable expansion
    for var in cfg:
        for production in cfg[var]:
            transitions[("q1", "", var)].append(("q1", production))

    # Terminal matching - dynamically for all terminals
    for terminal in terminals:
        transitions[("q1", terminal, terminal)].append(("q1", []))

    # Accept transition - don't push z back, just go to final state
    transitions[("q1", "", "z")].append(("qf", []))

    return transitions


# ---------------------------
# Step 3: NPDA Simulation
# ---------------------------
def simulate(npda, string, max_depth=1000):
    # state, input index, stack, depth
    queue = deque()
    queue.append(("q0", 0, ["z"], 0))
    
    # Less aggressive cycle detection - only track (state, input_pos, stack_height)
    visited = set()

    while queue:
        state, i, stack, depth = queue.popleft()
        
        # Depth limiting to prevent infinite recursion
        if depth > max_depth:
            continue
            
        # Accept condition - check if we're in accept state with all input consumed
        if state == "qf" and i == len(string):
            return "accept"

        if not stack:
            continue

        top = stack[-1]
        
        # Lighter cycle detection - only check key state info
        state_key = (state, i, len(stack), top)
        if state_key in visited:
            continue
        visited.add(state_key)

        # Try all transitions
        for (s, inp, st_top), moves in npda.items():
            if s == state and st_top == top:

                # Match input or epsilon
                if inp == "" or (i < len(string) and inp == string[i]):

                    for new_state, push_list in moves:
                        new_stack = stack[:-1]  # pop the top

                        # Push new symbols (in reverse order for stack)
                        if push_list:  # Only if there's something to push
                            for sym in reversed(push_list):
                                if sym:  # Don't push empty strings
                                    new_stack.append(sym)

                        new_i = i + (1 if inp != "" else 0)

                        queue.append((new_state, new_i, new_stack, depth + 1))

    return "reject"


# ---------------------------
# Example Usage
# ---------------------------
cfg_input = [
    "S -> XaXaX",
    "X -> aXb|bXa|XX|empty"
]

cfg = parse_cfg(cfg_input)
npda = build_npda(cfg)

# Debug: Print CFG and NPDA
print("CFG:")
for var, productions in cfg.items():
    for prod in productions:
        prod_str = ''.join(prod) if prod else 'ε'
        print(f"  {var} -> {prod_str}")

print("\nNPDA Transitions:")
for (state, inp, stack_top), moves in npda.items():
    inp_str = inp if inp else 'ε'
    for new_state, push_list in moves:
        push_str = ''.join(push_list) if push_list else 'ε'
        print(f"  ({state}, {inp_str}, {stack_top}) -> ({new_state}, {push_str})")

# Test strings
tests = ["ab", "abba", "aaabbb", "", "aaa", "bbb", "aabb"]

print("\nTest Results:")
for t in tests:
    result = simulate(npda, t)
    test_str = t if t else 'ε'
    print(f"  '{test_str}': {result}")