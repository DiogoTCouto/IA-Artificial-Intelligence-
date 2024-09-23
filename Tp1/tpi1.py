#STUDENT NAME:Diogo Tomás Rebelo Couto
#STUDENT NUMBER: 104288

#DISCUSSED TPI-1 WITH: (names and numbers):


import math
from tree_search import *

# Um state é um tuplo (cidade_atual, [set de cidades por visitar])
class OrderDelivery(SearchDomain):

    def __init__(self,connections, coordinates):
        self.connections = connections
        self.coordinates = coordinates
        # ANY NEEDED CODE CAN BE ADDED HERE

    def actions(self,state):
        city = state[0]
        actlist = []
        for (C1,C2,D) in self.connections:
            if (C1==city):
                actlist += [(C1,C2)]
            elif (C2==city):
               actlist += [(C2,C1)]
        return actlist 

    def result(self,state,action):
        #IMPLEMENT HERE
        (C1,C2) = action
        if C1 == state[0]:
            targets = state[1].copy()
            targets.discard(C2)
            return (C2, targets)

    def satisfies(self, state, goal):
        #IMPLEMENT HERE
        return state[0] == goal[0] and len(state[1]) == len(goal[1])

    def cost(self, state, action):
        #IMPLEMENT HERE
        C1, C2 = action
        if C1 == state[0]:
            for (x1, x2, d) in self.connections:
                if (x1, x2) == action or (x2, x1) == action:
                    return d

    def heuristic(self, state, goal):
        #IMPLEMENT HERE 
        current_city = state[0]
        targets = state[1].copy()
        
        points = len(targets) * 200
        
        if points == 0:
            targets = {goal[0]}
        
        distance_closest_target = 1000000
        for city in targets:
            c1_x, c1_y = self.coordinates[current_city]
            c2_x, c2_y = self.coordinates[city]
            distance = round(math.hypot(c1_x - c2_x, c1_y - c2_y))
            
            if distance < distance_closest_target:
                distance_closest_target = distance

        return points + distance_closest_target
 
class MyNode(SearchNode):

    def __init__(self,state,parent, depth=None, cost=None, heuristic=None, arg6=None):
        super().__init__(state,parent)
        self.depth = depth
        self.cost = cost
        self.heuristic = heuristic
        self.eval = cost + heuristic
        #ADD HERE ANY CODE YOU NEED

class MyTree(SearchTree):

    def __init__(self, problem, strategy='breadth',maxsize=0):
        super().__init__(problem,strategy)
        self.terminals = None
        self.maxsize = maxsize
        # Recriar o nodo inicial
        root = MyNode(problem.initial, None, 0, 0, problem.domain.heuristic(problem.initial, problem.goal))
        self.open_nodes = [root]
        
        #ADD HERE ANY CODE YOU NEED

    def astar_add_to_open(self,lnewnodes):
        #IMPLEMENT HERE

        # Adicionar novos nodes a uma lista
        self.open_nodes.extend(lnewnodes)
        self.open_nodes.sort(key=sorting_key_astar)

    def search2(self):
        #IMPLEMENT HERE

        while self.open_nodes != []:
            # Retirar o primeiro node da lista dos pendentes
            current_node = self.open_nodes.pop(0)

            # Verificar se chegamos ao resultado pretendido
            if self.problem.goal_test(current_node.state):
                self.solution = current_node
                self.terminals = len(self.open_nodes) + 1
                return self.get_path(current_node)
            self.non_terminals += 1
            
            lnewnodes = []
            # Explorar outras opçoes
            # Action é (C1, C2)
            for action in self.problem.domain.actions(current_node.state):
                newstate = self.problem.domain.result(current_node.state, action)
                if newstate not in self.get_path(current_node):
                    # Guardar o valor da profundidade
                    depth = current_node.depth + 1
                    # Guardar o valor de quanto custou para chegarmos ao current_node
                    cost = current_node.cost + self.problem.domain.cost(current_node.state, action)
                    # Guardar o valor da possivel hipotese que falta para chegarmos ao goal
                    heuristic = self.problem.domain.heuristic(newstate, self.problem.goal)
                        
                    newnode = MyNode(newstate, current_node, depth, cost, heuristic)
                    lnewnodes.append(newnode)
            self.add_to_open(lnewnodes)
            self.manage_memory()
            
        # Se nao der para chegar a lado algum, entao return None
        return None
        

    def manage_memory(self):
        if self.strategy == 'A*' and self.maxsize > 0:
            
            tree_size = self.non_terminals + len(self.open_nodes)
            
            while tree_size > self.maxsize:
                # Dicionário onde parent é a key e a miníma eval é o value
                
                sibling_groups = {}
                for node in self.open_nodes:
                    if node.parent in sibling_groups:
                        if sibling_groups[node.parent] > node.eval:
                            sibling_groups[node.parent] = node.eval
                    else:
                        sibling_groups[node.parent] = node.eval
                        
                # Decidir qual grupo de irmãos vai ser apagado primeiro
                parent_to_add = next(iter(sibling_groups))
                for parent in sibling_groups:
                    if sibling_groups[parent] > sibling_groups[parent_to_add]:
                        parent_to_add = parent
                
                # Apagar os filhos de parent_to_add
                self.open_nodes = [node for node in self.open_nodes if node.parent != parent_to_add]
                # Adicionar pai se não for None
                if parent_to_add != None:
                    self.non_terminals -= 1
                    parent_to_add.eval = sibling_groups[parent_to_add]
                    self.open_nodes.append(parent_to_add)

                # Reordenar por eval
                self.open_nodes.sort(key=sorting_key_astar)
                
                # Recalcular tree_size
                tree_size = self.non_terminals + len(self.open_nodes)

    # if needed, auxiliary methods can be added here

def orderdelivery_search(domain, city, targets, strat = 'breadth', maxsize = 0):
    
    target_set = set(targets)
    initial_state = (city, target_set)
    goal_state = (city, {})
    
    p = SearchProblem(domain, initial_state, goal_state)
    t = MyTree(p, strat, maxsize)
    path = t.search2()
    path = [state[0] for state in path]
    return (t, path)

# If needed, auxiliary functions can be added here
# Organizar a lista com base no eval e no city names
def sorting_key_astar(node):
    return (node.eval, node.state[0])
