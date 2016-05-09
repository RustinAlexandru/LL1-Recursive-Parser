import string
import pprint
import collections
import matplotlib.pyplot as plt
import pydot
import uuid

string_input = "a a a b b a b $"
string_input = string_input.split()
look_position = 0


def read_grammar(_file):
    productions = []
    productions_options = collections.OrderedDict()

    with open(_file, 'r') as input_file:
        for line in input_file:
            line = line.replace('\n', '')
            production = line.split('->')
            terminal = production[0].strip(" " + string.punctuation)
            non_terminals = production[1].split('|')
            for non_terminal in non_terminals:
                # non_terminal = non_terminal.replace(' ', '')
                non_terminal = non_terminal.lstrip(' ').rstrip(' ')
                productions.append((terminal, non_terminal))
                if terminal not in productions_options:
                    productions_options[terminal] = [non_terminal]
                else:
                    productions_options[terminal] += [non_terminal]

        nonterminals = productions_options.keys()
        terminals = []

        for prod in productions:
            right_side = prod[1]
            for nonterminal in nonterminals:
                # right_side = right_side.translate(None, nonterminal)
                right_side = right_side.replace(nonterminal, '')
            right_side_terminals = right_side.split()
            for term in right_side_terminals:
                terminals.append(term)

        terminals = list(set(terminals))
        data = {
            'terminals': terminals,
            'nonterminals': nonterminals,
            'productions': productions,
            'production_options': productions_options,
        }
        return data


g = read_grammar('grammar.txt')


def lookahead():
    global look_position
    result = string_input[look_position]
    look_position += 1
    return result


start_pos = 0
l = lookahead()


def get_production_symbols(production):
    return production.split()


def is_terminal(symbol):
    return symbol in g["terminals"]


def is_nonterminal(symbol):
    return symbol in g["nonterminals"]


def get_nullables():
    nullables = {}
    nullables2 = nullables.copy()
    while True:  # loop until nullabes dictionary doesn't change
        for production in g["productions"]:
            rhs = get_rhs_of_prod(production)
            lhs = get_lhs_of_prod(production)
            if rhs == "eps":  # X -> eps clar nullable
                nullables[lhs] = True
            else:  # X ->  Y_1 Y_2 ... Y_n    daca toate Yi sunt nullable -> X e nullable
                if all(is_nullable(rhs_nonterminal,
                                   nullables) and is_nonterminal(
                    rhs_nonterminal) for rhs_nonterminal in
                       get_production_symbols(rhs)):
                    nullables[lhs] = True
        if set(nullables) == set(nullables2):
            break
        else:
            nullables2 = nullables.copy()

    return nullables


def is_nullable(symbol, nulls):
    return symbol in nulls.keys()


def get_rhs_of_prod(prod):
    return prod[1]


def get_lhs_of_prod(prod):
    return prod[0]


nullables = get_nullables()


def is_prod_simple(rhs):
    if ' ' not in rhs:
        return True
    return False


def get_first_sets():
    first_sets = {}
    for terminal in g["terminals"]:  # first_set(terminal) = terminal
        first_sets[terminal] = {terminal}

    for non_terminal in g["nonterminals"]:
        first_sets[non_terminal] = set()  # first_set(nonterminal) = 0

    gen = (prod for prod in g["productions"] if get_rhs_of_prod(prod) == 'eps')
    for prod in gen:  # X -> eps productions , add eps to first(x)
        lhs = get_lhs_of_prod(prod)
        first_sets[lhs].add("eps")

    for x in range(0, 10):
        for prod in g["productions"]:  # Ex, incepem cu E -> T Add
            lhs = get_lhs_of_prod(prod)
            rhs = get_rhs_of_prod(prod)  # String =/= terminal
            if not is_terminal(
                    rhs):  # daca nu e terminal ( gen productia e de forma E -> T Add )
                rhs = rhs.split()  # fac split pe ea: ex [T, Add]
                k = len(rhs)
                for i in range(0,
                               k):  # pentru fiecare simbol din productie ( t, add)
                    if rhs[i] != ' ':
                        set_be_added = set()  # first(E) = first(T) - {eps} ( t-> eps | t-> ceva, nu vrem eps)
                        set_be_added = first_sets[rhs[i]]
                        set_be_added -= {"eps"}
                        first_sets[lhs] |= set_be_added
                        if not is_nullable(rhs[i],
                                           nullables):  # daca T nu e nullable, break ( adica daca nu poate disparea, ala e firstu)
                            break
                if is_nullable(lhs, nullables):
                    first_sets[lhs].add("eps")
            else:  # X -> num for ex, simple production  e terminal
                first_sets[lhs].add(rhs)
                # if is_nullable(lhs, nullables):
                #     first_sets[lhs].add("eps")

    gen = (prod for prod in g["productions"] if get_rhs_of_prod(prod) == 'eps')
    for prod in gen:  # X -> eps productions , add eps to first(x)
        lhs = get_lhs_of_prod(prod)
        first_sets[lhs].add("eps")

    return first_sets


first_sets = get_first_sets()


def get_first_set_string(string):
    return_value = set()
    # string = string.split()
    if is_terminal(string):
        return_value |= first_sets[string]
        return return_value

    if (isinstance(string, str)):
        string = string.split()

    for i in range(len(string)):
        if string[i] != ' ':
            return_value |= first_sets[string[i]] - {"eps"}
            if "eps" not in first_sets[string[i]]:
                return return_value
    return_value.add("eps")
    return return_value


def get_follow_sets():
    follow_sets = {}

    for nterm in g["nonterminals"]:
        follow_sets[nterm] = set()

    starting_symbol = g["productions"][0][0]
    follow_sets[starting_symbol].add(
        "$")  # adaugam $ pentru follow(simbol_start)

    for i in range(0, 10):
        for prod in g["productions"]:
            rhs = get_rhs_of_prod(prod)
            rhs = rhs.split()
            lhs = get_lhs_of_prod(prod)
            for i in range(0, len(rhs) - 1):
                if is_nonterminal(rhs[i]):  # A -> alfa nonterminalB beta
                    set_to_add = get_first_set_string(rhs[i + 1:]) - {"eps"}
                    follow_sets[rhs[i]] |= set_to_add
                    if "eps" in get_first_set_string(rhs[i + 1:]):
                        follow_sets[rhs[i]] |= follow_sets[lhs]
            else:  # A -> alfa B
                if is_nonterminal(rhs[len(rhs) - 1]):
                    follow_sets[rhs[len(rhs) - 1]] |= follow_sets[lhs]

    return follow_sets


follow_sets = get_follow_sets()

syntax_error = False


def predict_production():
    production_predict = {}

    for term in g["terminals"]:
        for nterm in g["nonterminals"]:
            production_predict[(nterm, term)] = None

    for prod in g["productions"]:
        nonterminal = get_lhs_of_prod(prod)
        rhs = get_rhs_of_prod(prod)
        for terminal in get_first_set_string(rhs):
            production_predict[(nonterminal, terminal)] = (nonterminal, rhs)
        if "eps" in get_first_set_string(rhs):
            for symbol in follow_sets[nonterminal]:
                production_predict[(nonterminal, symbol)] = (nonterminal, rhs)
            if "$" in follow_sets[nonterminal]:
                production_predict[(nonterminal, "$")] = (nonterminal, rhs)
    return production_predict


predictions = predict_production()


def pick_production(lhs, rhs):
    return predictions[(lhs, rhs)]


def match(char):
    global syntax_error
    global l
    if l == char:  # daca lookahead coincide cu characterul de match
        return string_input[
                   look_position], syntax_error  # returnez string[l], fara eroare
    else:
        syntax_error = True  # returnez nimic, eroare
        return None, syntax_error


# def match_eps():
#     global syntax_error
#     global l
#     return string_input[look_position - 1]


def parse_initial(prod):
    global syntax_error
    parse(prod)
    if not l == string_input[
        -1]:  # daca nu am reusit sa parsez tot cuvantul, eroare
        print 'Syntax error!!'
        return
    if syntax_error:
        print 'Syntax error!!'
    else:
        print 'Accepted!!'


derivation = []

graph = None
visited_nodes = []
graph_nodes = []


def add_node_if_existing(graph, node, terminal_node):
    if graph.get_node(node.get_name()):
        if terminal_node:
            new_node = pydot.Node(str(uuid.uuid1()),
                                  label=node.obj_dict['attributes']['label'],
                                  style='filled', fillcolor='#ffff00')
        else:
            new_node = pydot.Node(str(uuid.uuid1()),
                                  label=node.obj_dict['attributes']['label'])
        graph.add_node(new_node)
        graph_nodes.append(new_node)
        return new_node
    else:
        graph.add_node(node)
        graph_nodes.append(node)
        return node


def search_and_get_first_unvisited_node(graph, label):
    result = []
    node_list = graph_nodes
    for node in node_list:
        if node.get_name() not in visited_nodes and node.obj_dict['attributes'][
            'label'] == label:
            result.append(node)
    if len(result) >= 2:
        return result[0]
    else:
        return result


def get_node_by_label(graph, label):
    result = []
    for node in graph.get_node_list():
        if node.obj_dict['attributes']['label'] == label:
            result.append(node)
    return result


def parse(prod):
    global start_pos
    global l
    global syntax_error
    global derivation
    global graph
    global visited_nodes

    rhsterms = get_rhs_of_prod(prod).split()
    lhsterm = get_lhs_of_prod(prod)
    start_pos = 0
    for term in rhsterms:
        if is_terminal(term):
            if term == "eps":  # daca e eps, facem backtrack prin return
                # l = match_eps()
                # prod = pick_production(lhsterm, l)
                # parse(word, prod)
                return
            else:
                l, error = match(
                    term)  # daca e terminal, facem match si mergem mai departe
                if error:
                    return
                l = lookahead()
        else:  # term is nonterminal , daca e neterminal, alegem urmatoarea productie
            prod = pick_production(term, l)
            # derivation = rhsterms
            prod_terms = prod[1].split()
            # derivation.extend(rhsterms)
            # derivation.insert(0, prod_terms)
            if "eps" in prod_terms:  # cand afisam derivarea, daca avem X->eps, dispare X din derivare
                t = prod[0]
                derivation.remove(t)
            else:
                derivation = derivation[
                             :look_position - 1] + prod_terms + derivation[
                                                                look_position:]  # inlocuim in derivare neterminalul cu termenii productiei
            print " ".join(str(x) for x in derivation)

            starting_node = get_node_by_label(graph, prod[0])
            if isinstance(starting_node, list):
                starting_node = search_and_get_first_unvisited_node(graph,
                                                                    prod[0])
                if isinstance(starting_node, list):
                    starting_node = starting_node[0]

            visited_nodes.append(starting_node.get_name())
            for p_term in prod_terms:
                if is_terminal(p_term):  # terminalele le coloram
                    node_t = pydot.Node(str(p_term), label=str(p_term),
                                        shape='box', style='filled',
                                        fillcolor='#ffff00')
                else:
                    node_t = pydot.Node(str(p_term), label=str(p_term),
                                        shape='box')
                node_t = add_node_if_existing(graph, node_t,
                                              is_terminal(p_term))
                graph.add_edge(pydot.Edge(starting_node, node_t))

            if prod is None:  # daca nu exista nici o productie corespunzatoare, eroare
                syntax_error = True
                return
            parse(prod)  # continuam recursia cu productia urmatoare


if __name__ == '__main__':

    print 'Afisam gramatica'
    print '-----------------------'

    pprint.pprint(read_grammar('grammar.txt'), indent=4, depth=4)
    # starting_prod_symbol = grammar["nonterminals"][0]
    # starting_prod_options = grammar["production_options"][starting_prod_symbol]
    # print starting_prod_options[0][0]
    # print first_sets(g["productions"][1][1])
    # print get_rhs_of_prod(g["productions"][0])
    # print get_nullables()
    print '-----------------------'
    print 'Afisam first_seturile'

    print first_sets

    print '-----------------------'
    print 'Afisal follow seturile'
    f = get_follow_sets()
    pprint.pprint(f, indent=4, depth=4)
    start = g["productions"][0][0]
    start_prod = pick_production(start, l)
    derivation.extend(start_prod[1].split())

    print '-----------------------'
    print 'Cuvantul testat este:'
    print " ".join(str(x) for x in string_input)
    print '-----------------------'

    print 'Afisam derivarea'
    print '-----------------------'

    graph = pydot.Dot(graph_type='digraph', nodesep='2.5')
    node_from = pydot.Node(str(uuid.uuid1()), label=str(start))
    graph.add_node(node_from)
    graph_nodes.append(node_from)
    visited_nodes.append(node_from.get_name())
    for term in derivation:
        if is_terminal(term):  # coloram special daca e terminal
            node_to = pydot.Node(str(term), label=str(term), shape='box',
                                 style='filled', fillcolor='#ffff00')
        else:
            node_to = pydot.Node(str(term), label=str(term), shape='box')
        node_to = add_node_if_existing(graph, node_to, is_terminal(term))
        # graph.add_node(node_to)
        # visited_nodes.append(node_to.get_name())
        graph.add_edge(pydot.Edge(node_from, node_to))

    print start
    print " ".join(str(x) for x in derivation)
    # pprint.pprint(predictions, indent=4, depth=4)
    parse_initial(start_prod)

    graph.write_png('tree.png')

    print 'Derivarea finala: '
    print " ".join(str(x) for x in derivation)



