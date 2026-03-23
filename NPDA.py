from collections import defaultdict, deque
import os

def CFG_to_NPDA(cfg):
    initialState = cfg.split("->")[0].strip() # first we get the intial state
    # parese thorugh the CFG symbols into a dict for later
    productions = defaultdict(list)
    for line in cfg.splitlines():
            left, right = line.split("->")
            left = left.strip()
            for rule in right.split("|"):
                productions[left].append(rule.strip())
    transformedNPDA = ""
    transformedNPDA += (",q1-empty-z-" + str(initialState) + "z->q2") # start the NPDA off with the intial transition. Has start symbol and bottom marker for later construciton.
    maxState = 1
    loopCounter = 0
    # loops thorugh nonterminals and their productions to build the NPDA transitions
    for nonTerminal in productions:
        for rule in productions[nonTerminal]:
            if len(rule) == 1 or rule == "empty" or len(rule) == 2 and str(rule[1]) == str(nonTerminal):
                if loopCounter == 0:
                    transformedNPDA += (",q2") # adds state q2 as the first processing state
                loopCounter += 1
        # the seceond pass goes thorugh and builds the trantions in the correct format. ex (q2, ε, A) → (q2, α) is represented as q2-empty-A-α->q2
        for rule in productions[nonTerminal]:
            if len(rule) == 1 or rule == "empty" or len(rule) == 2 and str(rule[1]) == str(nonTerminal):
                if loopCounter != 0:
                    #multiple unit productions: separate with '|'
                    transformedNPDA += ("-empty-" + nonTerminal + "-" + str(rule) + "|")      
                else:
                    #single unit production: complete the transition
                    transformedNPDA += ("-empty-" + nonTerminal + "-" + str(rule) + "->q2")
    
    # this loops thorugh and adds tranitions for each terminal symbol in the productions. ex (q2, a, a) → (q2, ε) is represented as q2-empty-a-a->q2. 
    transformedNPDA += ("-a-a-empty|")
    transformedNPDA += ("-b-b-empty->q2,q2-empty-z-z->q3")
    maxState = 3
    for nonTerminal in productions:
        for rule in productions[nonTerminal]:
            currentState = 3
            if len(rule) > 1 and rule != "empty" and not (len(rule) == 2 and str(rule[1]) == str(nonTerminal)):
                maxState += 1
                transformedNPDA += (",q2-empty-" + nonTerminal + "-" + str(rule[-1]) + "->q" + str(maxState))
                currentState = maxState
                
                for i in range(len(rule)-2, -1, -1):
                    if i == 0:
                        # this checks if we are at the end of the production and if so it completes the transition to q2. ex (q2, ε, A) → (q2, α) is represented as q2-empty-A-α->q2
                        transformedNPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q2")
                    else:
                        # make a new state and add a trantion if we are not at the end of the production
                        maxState += 1
                        transformedNPDA += (",q" + str(currentState) + "-empty-" + str(rule[i+1]) + "-" + str(rule[i]) + str(rule[i+1]) + "->q" + str(maxState))
                        currentState = maxState
    if maxState > 3:
        # add intermediate states the the beginning of the NPDA string to ensure they are recognized as states in the final NPDA representation.
        for i in range(maxState - 3):
            transformedNPDA = ",q" + str(maxState - i) + transformedNPDA
    # final NPDA is build by taking putting the sates infront of the NPDA we built for formatting.
    transformedNPDA = "q1,q2,q3f" + transformedNPDA

    return transformedNPDA

def Run_NPDA(npda, string):
    parts = npda.split(',')
    startingState = parts[0] 
    
    # finn wehre tranitions start and states end.
    endPtr = 0
    for i, part in enumerate(parts):
        if '->' in part:
            endPtr = i
            break
    
    # stores all the accpeting states for faster access later. 
    acceptingStates = set()
    
    for i in range(endPtr):
        state = parts[i]
        if state.endswith('f'):
            cleanState = state[:-1]  # Remove 'f'
            acceptingStates.add(cleanState)
    
    transitions = defaultdict(list)
    # reconstructs transition string from remaining parts
    transitionParts = parts[endPtr:]
    
    # adds commas for easier reading between trantions.
    tranitionList = []
    currTranition = ""
    
    for part in transitionParts:
        if currTranition:
            currTranition += "," + part
        else:
            currTranition = part
            
        if '->' in currTranition:
            tranitionList.append(currTranition)
            currTranition = ""
    
    # parses each tranition
    for trans in tranitionList:
        if '->' not in trans:
            continue
            
        left, right = trans.split('->')
        right = right.strip()
        
        # handles tranitions with multiple stack operations
        if '|' in left:
            sourceTransitions = left.split('|')
            # get the state from the first transition
            firstTransitionParts = sourceTransitions[0].strip().split('-')
            if len(firstTransitionParts) >= 1:
                baseState = firstTransitionParts[0]
            else:
                continue
                
            # reconstructs full transitions for next parts
            reconTransitions = []
            for i, sourceTrans in enumerate(sourceTransitions):
                sourceTrans = sourceTrans.strip()
                if not sourceTrans:
                    continue
                    
                if i == 0:
                    # first transition is complete
                    reconTransitions.append(sourceTrans)
                else:
                    # prefixes subsequent transitions if needed.
                    if sourceTrans.startswith('-'):
                        reconTransitions.append(baseState + sourceTrans)
                    else:
                        reconTransitions.append(sourceTrans)
        else:
            reconTransitions = [left.strip()]
            
        for sourceTrans in reconTransitions: # continue building the transition list for the NPDA.
            sourceTrans = sourceTrans.strip()
            if not sourceTrans:
                continue
                
            partsTrans = sourceTrans.split('-')
            if len(partsTrans) >= 4:
                state = partsTrans[0]
                inputSym = partsTrans[1] if partsTrans[1] != 'empty' else ''
                stackTop = partsTrans[2] if partsTrans[2] != 'empty' else ''
                newStack = '-'.join(partsTrans[3:]) if partsTrans[3] != 'empty' else ''
                
                transitions[state].append({ 'input': inputSym, 'stackTop': stackTop, 'new_stack': newStack, 'nextState': right })
    
    stringLength = len(string)
    queue = deque([(startingState, 0, ('z',), 0)])
    
    # visted set to make it so we dont revist the same config multiple times(infintie loops).
    visited = set()
    
    while queue:
        currState, inputPosition, stackTuple, depth = queue.popleft()
        #print(f"Current state: {currState}, Input position: {inputPosition}, Stack: {stackTuple}, Depth: {depth}") # debugging print
        if depth >= 50:  # depth limit
            continue
        # create config  key for visted set
        configKey = (currState, inputPosition, stackTuple)
        if configKey in visited:
            #print(f"Already visited: {configKey}, skipping...") # debugging print
            continue
        visited.add(configKey)
        
        # checks accpeting state and if the input is fully read
        if (currState in acceptingStates and inputPosition == stringLength):
            return 'accept'
        
        # trys all trnaitons for the current state. if the transition is valid it adds the new config to the queue for processing.
        if currState in transitions:
            for transition in transitions[currState]:
                inputSym = transition['input']
                stackTop = transition['stackTop']
                newStackSym = transition['new_stack']
                nextState = transition['nextState']
                
                # checks input consumption
                doesApply = False
                newInputPosition = inputPosition
                # lamda trantion logic
                if inputSym == '': 
                    doesApply = True
                elif inputPosition < stringLength and string[inputPosition] == inputSym:
                    newInputPosition = inputPosition + 1
                    doesApply = True
                else:
                    continue
                
                # check stack operations
                stackList = list(stackTuple)
                # stack logic
                if stackTop == '':
                    if newStackSym:
                        # push in reverse order since stack is LIFO
                        for sym in reversed(newStackSym):
                            stackList.append(sym)
                elif stackList and stackList[-1] == stackTop:
                    # pops symbol 
                    stackList.pop()
                    # pushes symbol 
                    if newStackSym:
                        for sym in reversed(newStackSym):
                            stackList.append(sym)
                elif not stackList and stackTop == 'z':
                    # special case for trying to match bottom marker when stack is empty
                    continue
                else:
                    continue
                
                # makes new config and adds it to the queue if it has not already been visted.
                if doesApply:
                    newStackTuple = tuple(stackList)
                    newConfig = (nextState, newInputPosition, newStackTuple)
                
                    # only add if not already visited (additional check for efficiency)
                    if newConfig not in visited and len(newStackTuple) < 15:
                        queue.append((nextState, newInputPosition, newStackTuple, depth + 1))
    
    return 'reject'
    #used ai to get a grasp of the high level overview of the code to get an idea of the structure and how to parse the NPDA.
def parse_automaton_to_dict(automatonString, automatonType):
    
    # split into states and transitions
    parts = automatonString.split(',')
    statesString = parts[0]
    
    # parse states from concatenated format
    def parse_states_from_string(statesStr):
        states = []
        acceptingStates = set()
        i = 0
        currState = ""
        
        while i < len(statesStr):
            char = statesStr[i]
            
            if char.isalpha() and char.islower() and currState == "":
                # start of new state
                currState += char
            elif char.isdigit():
                # part of state name
                currState += char
            elif char == 'f':
                # accept state marker
                if currState:
                    states.append(currState + 'f')
                    acceptingStates.add(currState)
                    currState = ""
            elif char.isalpha() and char.islower() and currState != "":
                # start of next state
                if currState:
                    states.append(currState)
                currState = char
            
            i += 1
        
        # add final state if it exists
        if currState:
            states.append(currState)
        
        return states, acceptingStates
    
    states, acceptingStates = parse_states_from_string(statesString)
    
    # parse transitions
    transitions = {}
    transitionList = []
    # loops thorugh the tranition parts and puts them in a dict
    for i in range(1, len(parts)):
        transPart = parts[i]
        if '->' in transPart:
            left, right = transPart.split('->')
            right = right.strip()
            
            if automatonType == "NPDA":
                # handle NPDA transitions with stack operations
                if '|' in left:
                    # logic formultiple stack operations
                    operations = left.split('|')
                    baseState = None
                    baseInput = None
                    
                    for j, op in enumerate(operations):
                        op = op.strip()
                        opParts = op.split('-')
                        
                        if j == 0:
                            # first operation has state
                            if len(opParts) >= 4:
                                baseState = opParts[0]
                                baseInput = opParts[1] if opParts[1] != 'empty' else ''
                                stackTop = opParts[2]
                                stackPush = opParts[3]
                                
                                transitionInfo = {'from_state': baseState, 'input': baseInput, 'stackTop': stackTop, 'stack_push': stackPush, 'to_state': right
                                }
                                transitionList.append(transitionInfo)
                        else:
                            # logic for subsequent operations
                            if len(opParts) >= 3:
                                inputSym = opParts[0] if opParts[0] != 'empty' else ''
                                stackTop = opParts[1]
                                stackPush = opParts[2]
                                
                                # process all operations regardless of input symbol
                                transitionInfo = {'from_state': baseState,'input': inputSym,'stackTop': stackTop,'stack_push': stackPush,'to_state': right
                                }
                                transitionList.append(transitionInfo)
                else:
                    # single operation
                    opParts = left.strip().split('-')
                    if len(opParts) >= 4:
                        fromState = opParts[0]
                        inputSym = opParts[1] if opParts[1] != 'empty' else ''
                        stackTop = opParts[2]
                        stackPush = opParts[3]
                        
                        transitionInfo = {'from_state': fromState,'input': inputSym,'stackTop': stackTop,'stack_push': stackPush,'to_state': right
                        }
                        transitionList.append(transitionInfo)
            else:
                # NFA transitions with support for "or" inputs
                leftParts = left.split('-')
                if len(leftParts) >= 2:
                    fromState = leftParts[0]
                    inputSym = leftParts[1]
                    
                    # handle multiple inputs separated by |
                    if '|' in inputSym:
                        # Split by | and create separate transitions for each input
                        inputOptions = inputSym.split('|')
                        for inputOption in inputOptions:
                            inputOption = inputOption.strip()
                            transitionInfo = {'from_state': fromState,'input': inputOption,'to_state': right
                            }
                            transitionList.append(transitionInfo)
                    else:
                        # single input transition
                        transitionInfo = {'from_state': fromState,'input': inputSym,'to_state': right
                        }
                        transitionList.append(transitionInfo)
    
    # group  the transitions by source state
    for trans in transitionList:
        fromState = trans['from_state']
        if fromState not in transitions:
            transitions[fromState] = []
        transitions[fromState].append(trans)
    
    # build the result dictionary
    result = {
        'states': states,
        'acceptingStates': acceptingStates,
        'transitions': transitions,
    }
    
    return result

def Intersection_NPDA_NFA(npda, nfa):
    finalNpda = ""
    # parse both automata into dictionaries for easier processing
    npdaDict = parse_automaton_to_dict(npda, "NPDA")
    nfaDict = parse_automaton_to_dict(nfa, "NFA")
    
    npdaStates = npdaDict['states']
    npdaTransitions = npdaDict['transitions']
    
    nfaStates = nfaDict['states']
    nfaTransitions = nfaDict['transitions']
    #loops thorugh states to build the product state set and marks accept states.
    for npdaState in npdaStates:
        for nfaState in nfaStates:
            if npdaState.endswith('f') and nfaState.endswith('f'):
                # if for when both  the npda and nfa are accepting states.
                finalNpda += nfaState[:-1] + npdaState + ','
            elif nfaState.endswith('f'):
                # if the nfa accepts but the npda does not strip the f so the product state does not accept.
                finalNpda += nfaState[:-1] + npdaState + ','
            elif npdaState.endswith('f'):
                # if the npda accepts but the nfa does not strip the f so the product state does not accept.
                finalNpda += nfaState + npdaState[:-1] + ','
            else:
                # Neither accepting: concatenate as-is
                finalNpda += nfaState + npdaState + ','
    #loops thorugh sstates and trantions to make the product trantions for the new NPDA.
    for npdaStateName in npdaTransitions:
        for nfaStateName in nfaTransitions:
            for npdaTrans in npdaTransitions[npdaStateName]:
                for nfaTrans in nfaTransitions[nfaStateName]:
                    if npdaTrans['input'] == nfaTrans['input']:
                        #if both transitions consume the same terminal add a product transition to the new NPDA
                        finalNpda += nfaTrans['from_state'] + npdaTrans['from_state'] + '-' + npdaTrans['input'] + '-' + npdaTrans['stackTop'] + '-' + npdaTrans['stack_push'] + '->' + nfaTrans['to_state'] + npdaTrans['to_state'] + ','
                    if npdaTrans['input'] == '':
                        # if the NPDA makes an lamda tranition add a product trantion where the NFA doesnt move and the NPDA makes its lamda tranition.
                        finalNpda += nfaTrans['from_state'] + npdaTrans['from_state'] + '-empty-' + npdaTrans['stackTop'] + '-' + npdaTrans['stack_push'] + '->' + nfaTrans['to_state'] + npdaTrans['to_state'] + ','

    finalNpda = finalNpda[:-1] 
    return finalNpda 
#used ai to help make reading and writing text files eaiser.
baseDir = os.path.dirname(os.path.abspath(__file__)) # file path to make nagivating to test files eaiser

testCases = [
    {
        "name": "Test Case 1",
        "cfg_file": "test_case_1_cfg.txt",
        "strings": ["aababb", "aaaaabbbbb"],
    },
    {
        "name": "Test Case 2",
        "cfg_file": "test_case_2_cfg.txt",
        "strings": ["baabba", "aaabbb"],
    },
    {
        "name": "Test Case 3",
        "cfg_file": "test_case_3_cfg.txt",
        "strings": ["bbaabaaaaa", "abaaba"],
    },
    {
        "name": "Test Case 4",
        "cfg_file": "test_case_4_cfg.txt",
        "strings": ["baabaa", "abaabab"],
    },
    {
        "name": "Test Case 5",
        "cfg_file": "test_case_5_cfg.txt",
        "strings": ["bbbaab", "aababbb"],
    },
]
# loops thorugh test cases for part 1. it reads the inputs from text files and outputs the results to the console and a text file.
for case in testCases:
    cfgPath = os.path.join(baseDir, case["cfg_file"])

    with open(cfgPath, "r", encoding="utf-8") as cfgFile:
        cfgText = cfgFile.read().strip()

    print(f"\n=== {case['name']} ===")
    print("CFG input:")
    print(cfgText)

    npdaResult = CFG_to_NPDA(cfgText)
    print("\nCFG output (NPDA):")
    print(npdaResult)

    npdaOutputFilename = f"{case['name'].lower().replace(' ', '_')}_npda_output.txt"
    npdaOutputPath = os.path.join(baseDir, npdaOutputFilename)
    with open(npdaOutputPath, "w", encoding="utf-8") as npdaOutputFile:
        npdaOutputFile.write(npdaResult + "\n")

    print("\nNPDA test results:")
    for testStr in case["strings"]:
        result = Run_NPDA(npdaResult, testStr)
        print(f"String '{testStr}': {result}")


intersectionTestCases = [
    {
        "name": "Intersection Test Case 1",
        "automata_file": "intersection_test_case_1_automata.txt",
        "strings": ["aabbaa", "aaaa"],
    },
    {
        "name": "Intersection Test Case 2",
        "automata_file": "intersection_test_case_2_automata.txt",
        "strings": ["baaba", "baaaab"],
    },
    {
        "name": "Intersection Test Case 3",
        "automata_file": "intersection_test_case_3_automata.txt",
        "strings": ["baaa", "aabaaab"],
    },
    {
        "name": "Intersection Test Case 4",
        "automata_file": "intersection_test_case_4_automata.txt",
        "strings": ["bbaaa", "baaabbb"],
    },
    {
        "name": "Intersection Test Case 5",
        "automata_file": "intersection_test_case_5_automata.txt",
        "strings": ["aabbaab", "aaabbb"],
    },
]

# loops thorugh the test cases for part 2. reads the NPDA and NFA from a text file, makes the intersection NPDA, then tests the cases and outputs the results to the console and a text file.
def load_intersection_automata(filePath):
    with open(filePath, "r", encoding="utf-8") as automataFile:
        lines = [line.strip() for line in automataFile if line.strip()]
    return lines[0], lines[1]

for case in intersectionTestCases:
    filePath = os.path.join(baseDir, case["automata_file"])
    nfa_input, npda_input = load_intersection_automata(filePath)

    print(f"\n=== {case['name']} ===")
    print("NFA input:")
    print(nfa_input)
    print("NPDA input:")
    print(npda_input)

    newNPDA = Intersection_NPDA_NFA(npda_input, nfa_input)
    print("\nIntersection output (NPDA):")
    print(newNPDA)

    intersectionOutputFilename = f"{case['name'].lower().replace(' ', '_')}_intersection_npda_output.txt"
    intersectionOutputPath = os.path.join(baseDir, intersectionOutputFilename)
    with open(intersectionOutputPath, "w", encoding="utf-8") as intersectionOutputFile:
        intersectionOutputFile.write(newNPDA + "\n")

    print("\nIntersection NPDA test results:")
    for testStr in case["strings"]:
        result = Run_NPDA(newNPDA, testStr)
        print(f"String '{testStr}': {result}")