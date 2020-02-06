
class anyon_node(object):
    '''
    Anyon node object - element in the aj-tree
    var id          id number (loc)

    var cons        connections, in the form:
                        [node, edge]

    var s           size, number of growth iterations
    var g           growth state \ parity of s
    var p           parity of node
    var d           delay, iterations to wait
    var w           waited, iterations already waited
    var bucket      indicator to grow node size once per bucket
    var calc_delay  list of children nodes with undefined delay
    '''

    def __init__(self, id):

        self.type = "A"
        self.id = id

        self.boundary = [[], []]
        self.cons = []
        self.s = 0
        self.p = 0
        self.d = 0
        self.w = 0
        self.calc_delay = []

    @property
    def g(self):
        return self.s % 2

    def __repr__(self):
        type = "s" if self.id[0] == 0 else "p"
        return self.type + type + "{},{}".format(self.id[1], self.id[2])


class junction_node(anyon_node):
    '''
    inherit all methods from anyon_node
    add list of anyon-nodes
    '''
    def __init__(self, id):
        super().__init__(id)
        self.type = "J"

class boundary_node(anyon_node):
    '''
    inherit all methods from anyon_node
    add list of anyon-nodes
    '''
    def __init__(self, id):
        super().__init__(id)
        self.type = "B"
        self.p = 1


class empty_node(anyon_node):
    '''
    inherit all methods from anyon_node
    add list of anyon-nodes
    '''
    def __init__(self, id):
        super().__init__(id)
        self.type = "E"
        self.dis = 0


def comp_tree_p_of_node(node, ancestor=None):
    '''
    Recursive function to find the parity of a node and its children
    '''
    parity = sum([1 - comp_tree_p_of_node(con[0], node) for con in node.cons if con[0] is not ancestor]) % 2
    
    if type(node) == anyon_node:
        node.p = parity
        return node.p

    elif type(node) == junction_node:
        node.p = 1 - parity
        return node.p

    else:
        node.p = 1
        return node.p


def comp_tree_d_of_node(node, cluster, an_con=None):
    '''
    Recursive function to find the delay of a node and its children
    '''
    node.calc_delay = []
    node.w = 0

    if an_con is None:
        for con in node.cons:
            comp_tree_d_of_node(cluster, con[0], [node, con[1]])
    else:
        ancestor, edge = an_con
        # size_diff = (node.s + node.g)//2 - (ancestor.s + node.g)//2 + edge*(-1)**(node.p + 1)
        # support_fix = (node.g + ancestor.g)%2
        # node.d = ancestor.d + 2 * size_diff - support_fix - 1
        node.d = ancestor.d + (node.s//2 - ancestor.s//2 + edge*(-1)**(node.p + 1))


        if node.d < cluster.mindl:                  # store cluster minimum delay
            cluster.mindl = node.d

        for con in node.cons:
            if con[0] is not ancestor:
                comp_tree_d_of_node(cluster, con[0], [node, con[1]])


def connect_nodes(nodeA, nodeB, edge):
    nodeA.cons.append([nodeB, edge])
    nodeB.cons.append([nodeA, edge])


def adoption(ac_vertex, pa_vertex, ac_cluster, pa_cluster):
    '''
    var ac_vertex   merging vertex of base cluster
    var pa_vertex   merging vertex of grow cluster
    '''
    ac_node, pa_node = ac_vertex.node, pa_vertex.node
    even_after_union = True if ac_cluster.parity % 2 == pa_cluster.parity % 2 else False

    '''
    ac_node:    root of active vertex
    pa_node:    root of passive vertex
    an_node:    ancestor node during union
    ch_node:    child node during union

    even_after_union:       if cluster is even after union, union of trees is done by weighted union
                            else, union is done by always appending even tree to odd tree,
                            delay calculation is needed from the child node (of union duo) and descendents
    '''
    if not even_after_union and pa_cluster.parity % 2 == 0:
        root_node, an_node, ch_node = ac_cluster.root_node, ac_node, pa_node
    else:
        root_node, an_node, ch_node = pa_cluster.root_node, pa_node, ac_node

    calc_delay_node = None if even_after_union else ch_node

    if ac_node.g == 0 and pa_node.s > 1:                             # Connect via new juntion-node
        pa_vertex.node = junction_node(pa_vertex.sID)
        an_edge = an_node.s // 2
        connect_nodes(pa_vertex.node, an_node, an_edge)
        connect_nodes(pa_vertex.node, ch_node, ch_node.s // 2)
        calc_delay_node = None if even_after_union else [pa_vertex.node, an_edge, an_node]
    else:                                                               # Connect directly
        an_edge = (an_node.s + ch_node.s) // 2
        connect_nodes(an_node, ch_node, an_edge)
        calc_delay_node = None if even_after_union else [ch_node, an_edge, an_node]

    root_node.calc_delay.append(calc_delay_node)                        # store generator of undefined delay

    return root_node
