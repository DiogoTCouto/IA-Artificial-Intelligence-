#encoding: utf8

# YOUR NAME: Diogo Couto
# YOUR NUMBER: 104288

# COLLEAGUES WITH WHOM YOU DISCUSSED THIS ASSIGNMENT (names, numbers):
# - ...
# - ...

from semantic_network import *
from constraintsearch import *



class MySN(SemanticNetwork):

    def __init__(self):
        SemanticNetwork.__init__(self)
        self.assoc_stats = {}
        # ADD CODE HERE IF NEEDED
        pass

    def query_local(self, user=None, e1=None, rel=None, e2=None):
        self.query_result = []

        for my_user in self.declarations:
            if (user == None or my_user == user):

                for (my_e1, my_rel) in self.declarations[my_user]:
                    if (e1 == None or my_e1 == e1) and (rel == None or my_rel == rel):
                        my_e2 = self.declarations[my_user][(my_e1, my_rel)]
                        if isinstance(my_e2, set):
                            for my_e2 in self.declarations[my_user][(my_e1, my_rel)]:
                                if (e2 == None or my_e2 == e2):
                                    self.query_result.append(Declaration(my_user, Relation(my_e1, my_rel, my_e2)))
                        elif (e2 == None or my_e2 == e2):
                            self.query_result.append(Declaration(my_user, Relation(my_e1, my_rel, my_e2)))
        return self.query_result

    def query(self, entity, assoc=None):
        self.query_result = []
        for my_user in self.declarations:
            for (my_e1, my_rel) in self.declarations[my_user]:
                my_e2 = self.declarations[my_user][(my_e1, my_rel)]
                if isinstance(my_e2, set):
                    for entity2 in my_e2:
                        if my_rel!='member' and my_rel!='subtype' and (assoc is None or my_rel == assoc) and (self.predecessor(my_e1, entity)):
                            self.query_result.append(Declaration(my_user, Relation(my_e1, my_rel, entity2)))
                else:
                    if my_rel!='member' and my_rel!='subtype' and (assoc is None or my_rel == assoc) and (self.predecessor(my_e1, entity)):
                        self.query_result.append(Declaration(my_user, Relation(my_e1, my_rel, entity2)))
        return self.query_result
    
    def predecessor(self, pre1: str, pre2: str):
        if pre1 == pre2:
            return True
        for my_user in self.declarations:
             for (my_e1, my_rel) in self.declarations[my_user]:
                my_e2 = self.declarations[my_user][(my_e1, my_rel)]
                if (my_rel == 'member' or my_rel == 'subtype' ) and my_e2 == pre1:
                    if self.predecessor(my_e1, pre2):
                        return True
        return False
    

    def get_type_path(self, entity: str, user = None): 
        for my_user in self.declarations:
             if my_user == user or user == None:
                for (my_e1, my_rel) in self.declarations[my_user]:
                    my_e2 = self.declarations[my_user][(my_e1, my_rel)]
                    if  (my_rel == 'member' or my_rel == 'subtype') and my_e1 == entity:
                        return [my_e2] + self.get_type_path(my_e2, user)
        return []
        

    def update_assoc_stats(self, assoc, user=None):
        assoc_stats1 = {}
        assoc_stats2 = {}
        unknown_1 = 0
        unknown_2 = 0
        objects1 = []
        objects2 = []

        relevant_declarations = self.query_local(rel = assoc, user = user)

        relevant_declarations = list( filter(lambda x:  ( x.relation.entity1[0].isupper() or x.relation.entity2[0].isupper() ) , relevant_declarations) )

        for my_decl in relevant_declarations:
            my_e1 = my_decl.relation.entity1
            my_e2 = my_decl.relation.entity2
            type_e1 = self.get_type_path(my_e1, user)
            type_e2 = self.get_type_path(my_e2, user)
 

            if my_e1 not in objects1:
                objects1.append(my_e1)
            if type_e1 == []:
                unknown_1 += 1

            if my_e2 not in objects2:
                objects2.append(my_e2)
            if type_e2 == []:
                unknown_2 += 1

            for type in type_e1:
                if type not in assoc_stats1.keys():
                    assoc_stats1[type] = 0
                assoc_stats1[type] += 1

            for type in type_e2:
                if type not in assoc_stats2.keys():
                    assoc_stats2[type] = 0
                assoc_stats2[type] += 1
                
        n_objects = len(relevant_declarations)

        for type in assoc_stats1:
            assoc_stats1[type] = assoc_stats1[type] / (n_objects - unknown_1 + unknown_1**(1/2) )
        for type in assoc_stats2:
            assoc_stats2[type] = assoc_stats2[type] / (n_objects - unknown_2 + unknown_2**(1/2) )

        self.assoc_stats[(assoc,user)] = (assoc_stats1, assoc_stats2)



class MyCS(ConstraintSearch):

    def __init__(self,domains,constraints):
        ConstraintSearch.__init__(self,domains,constraints)
        # ADD CODE HERE IF NEEDED
        pass

    def search_all(self,domains=None,xpto=None):
        # If needed, you can use argument 'xpto'
        # to pass information to the function
        #
        # IMPLEMENTAR AQUI

        possible_solutions = []

        # Variable ordering
        keys = list(self.domains.keys())
        keys.sort(key = lambda key: len(self.domains[key]) - 100 if (type(self.domains[key][0]) is tuple) else len(self.domains[key]))
        
        value = {}
        for key in keys:
            value[key] = None
        possible_solutions.append(value.copy())

        while(any(value[var] == None for var in value for value in possible_solutions)):
            for value in possible_solutions:
                if None in value.values():
                    possible_solutions.remove(value) 
                    
                    for current_key in keys:
                        if value[current_key] != None:
                            continue
                        for num in self.domains[current_key]:
                            value[current_key] = num

                            # Propagate restrictions
                            for key in keys:
                                if key == current_key:
                                    continue
                                if (current_key, key) in self.constraints:
                                    constraint = self.constraints[current_key, key]
                                    for num2 in self.domains[key]:
                                        if constraint(current_key, num, key, num2):
                                            value[key] = num2
                                            possible_solutions.append(value.copy())


        solutions = []
        # Final pass to check all constraints
        for value in possible_solutions:

            solution = True

            for key1 in keys:
                if not solution:
                    break
                for key2 in keys:
                    if key1 == key2:
                        continue
                    if (key1, key2) in self.constraints:
                        if not self.constraints[key1, key2](key1, value[key1], key2, value[key2]):
                            solution = False
                            break

            if solution:
                solutions.append(value.copy())

        return solutions

    def propagate(self, domains, var):
        for (x, y) in self.constraints:
            if y == var:
                new_cons = self.constraints[x, y]
                values = len(domains[x])
                domains[x] = [j for j in domains[x] if any(new_cons(x, j, y, val_i) for val_i in domains[y])]
                if len(domains[x]) < values:
                    self.propagate(domains, x)
        return domains    
