import StructTools

class ConstraintGraph():
    """
    Generates, stores and solves a constraint graph
    """    
    def __init__(self, variables:range | list, domain:set | dict[set], confilct_list:dict[list], hard_unary_constraints:list[tuple | None]=[], soft_unary_constraints=None, custom_domain_vals=lambda *args: (list(args[1]), list(args[2]), [tuple(args[1])], [tuple(args[2])]), custom_consist_check=None, solution=[]):
        """
        Initialises a constraint graph object

        Args:
            variables (range | list): list of variable names
            domain (set): initial possible set of values each variable can take
            confilct_list (dict[list]): Dict mapping variables to its associated entities (e.g. which courses are in a particular session); overlapping entities indicate conflict
            hard_unary_constraints (list[tuple  |  None], optional): List indicating values that particular variables must not take. Defaults to [].
            soft_unary_constraints (function, optional): Returns generator indicating which values variables must ideally not take; is dependent on current assignment. Defaults to None.
            solution (list, optional): Stores arrangement of previous resource (if current graph instantiated by recursive call). Defaults to [].
        """        
        self.__solution = solution
        self.__hard_unary_constraints = hard_unary_constraints
        self.__soft_unary_constraints = soft_unary_constraints
        self.__custom_domain_vals = custom_domain_vals
        self.__custom_consist_check = custom_consist_check
        self.__variables = variables
        
        # Formats input conflict_list
        self.__conflicts = self.getConflicts(confilct_list) 
        
        # Initialises hard and soft domains
        if type(domain) is set:
            self.__hard_domains = {var : domain for var in self.__variables}
            self.__soft_domains = {var : domain for var in self.__variables}
        else:
            self.__hard_domains = domain
            self.__soft_domains = domain

    def getConflicts(self, conflict_list:dict[list]):
        """
        Converts input conflict_list into list of tuples of form (variable_1, variable_2)
        
        Args:
            conflict_list (dict[list]): Input conflict_list

        Returns:
            list[tuple]: Formatted conflict list
        """
        # Initialises a set to keep track of conflicts and to automatically remove duplicates 
        conflicts = set()

        # Compare every variable with each other
        for x in conflict_list:
            for y in conflict_list:
                # Skips if they're the same
                if x == y:
                    continue
                
                # Adds conflict between x and y if they have any common associated entities
                if set(conflict_list[x]) & set(conflict_list[y]) != set():
                    conflicts.add((x, y))
        
        # Converts conflicts to list and returns
        return list(conflicts)
    
    def makeNodeConsistent(self, assignment:dict|None = None, hard=True):
        """
        Updates either hard_ or soft_domain to make every node consistent with the soft unary constraints
        If hard=False, then dependent on assignment

        Args:
            assignment (dict): Current assignment of values to variables
        """
        if hard:
            for constraint in self.__hard_unary_constraints:
                # Removes forbidden value from current node's hard domain
                # If value has already been removed, skip constraint
                try:
                    domain = self.__hard_domains[constraint[0]].copy()
                    if len(domain) == 0:
                        continue
                    
                    # If the values in the domain are tuples, remove each tuple if the
                    # forbidden value from the constraint is in it
                    if type(list(domain)[0]) is tuple:
                        to_remove = set()
                        for value in domain:
                            if constraint[1] in value:
                                to_remove.add(value)
                        
                        domain -= to_remove
                    # Otherwise, remove value in constraint from domain
                    else:
                        domain.remove(constraint[1])
                    
                    self.__hard_domains[constraint[0]] = domain
                except KeyError:
                    continue
        else:
            # Ends procedure if there aren't any soft constraints
            if self.__soft_unary_constraints is None:
                return
            
            for constraint in self.__soft_unary_constraints(assignment):
                # Removes forbidden value from current node's soft domain
                # If value has already been removed, skip constraint
                try:
                    # Gets the domain for the constrait's var
                    domain = self.__soft_domains[constraint[0]].copy()
                    if len(domain) == 0:
                        continue
                    
                    # If the values in the domain are tuples, remove each tuple if the
                    # forbidden value from the constraint is in it
                    if type(list(domain)[0]) is tuple:
                        to_remove = set()
                        for value in domain:
                            if constraint[1] in value:
                                to_remove.add(value)
                        
                        domain -= to_remove
                    # Otherwise, remove value in constraint from domain
                    else:
                        domain.remove(constraint[1])
                    
                    self.__soft_domains[constraint[0]] = domain
                except KeyError:
                    continue
    
    def revise(self, X, Y, hard=True):
        """
        Resolves binary constraints between variables X and Y for either hard or soft domains (depending on arguments)

        Args:
            X (variable): variable 1
            Y (variable): variable 2
            hard (bool, optional): Indicates whether to update hard_ or soft_domains. Defaults to True.

        Returns:
            bool: Indicates whether domains have been updated
        """
        # Returns False if this pair of vars isn't in conflicts
        if (X, Y) not in self.__conflicts:
            return False
        
        # revised defaults to False
        revised = False
        to_remove = set()
        
        # Updates hard_domains if hard is True; else updates soft_domains
        if hard:
            # Removes values from X's domain that result in binary constraint violation if chosen for all possible
            # choices of values from Y's domain
            for x in self.__hard_domains[X]:
                for y in self.__hard_domains[Y]:
                    if not self.isConflict(x, other=y):
                        break
                else:
                    to_remove.add(x)
                    revised = True
            
            self.__hard_domains[X] = self.__hard_domains[X].copy() - to_remove
        else:
            # Same as above
            for x in self.__soft_domains[X]:
                for y in self.__soft_domains[Y]:
                    if not self.isConflict(x, other=y):
                        break
                else:
                    to_remove.add(x)
                    revised = True
        
            self.__soft_domains[X] = self.__soft_domains[X].copy() - to_remove
            
        return revised
    
    def AC3(self, queue=[], hard=True):
        """
        Implementation of the AC3 algorithm

        Args:
            queue (list, optional): initial queue of constraints (used in inference). Defaults to [].
            hard (bool, optional): indicates whether to update hard_ or soft_domains. Defaults to True.

        Returns:
            bool: Indicates whether validity of current set of domains
        """
        # If queue isn't given, initialised as copy of conflicts
        queue = StructTools.deepCopy(self.__conflicts) if queue == [] else queue

        # Loops until queue is empty
        while len(queue) > 0:
            # Gets variables from current constraint and pops from queue
            X, Y = queue.pop(0)

            # Revises domains of X and Y based on binary constraints
            if self.revise(X, Y, hard):
                # If resulting domain (either soft or hard depending on argument) is empty, then 
                # current set of domains is invalid -> Returns False
                if hard:
                    if len(self.__hard_domains[X]) == 0:
                        #return X
                        return False
                else:
                    if len(self.__soft_domains[X]) == 0:
                        #return X
                        return False
                
                # Otherwise, enqueue all neighbours of X excluding Y
                # (since domain of X has been updated, there are possible violations of binary constraints
                # with other neighbours)
                for Z in self.neighbours(X) - {Y}:
                    queue.append((Z, X))
        
        # If no revisions result in invalid domains, return True
        #return None
        return True
    
    def neighbours(self, var):
        """
        Gets all neighbouring nodes to var

        Args:
            var (variable): Current node we need to find neighbours of

        Returns:
            set: Neighbours of var
        """   
        result = set()

        # Iterates through every arc in the graph
        for arc in self.__conflicts:
            # Adds other node in arc if var is in arc
            if var in arc:
                if arc[0] == var:
                    result.add(arc[1])
                else:
                    result.add(arc[0])
        
        # Returns set of neighbours
        return result
            
    def inference(self, assignment:dict, var, hard=False):
        """
        Infers the only possible assignments of particular variables using
        maintaining arc consistency algorithm.

        Args:
            assignment (dict): Current assignment of values to variables
            var (variable): current variables which has just been assigned a value (from backtrack method)

        Returns:
            tuple[dict]: Two dicts of inferences based on soft_ and hard_domains
        """
        # Gets neighbours to var
        neighbours = self.neighbours(var)
        inferences = dict()
        
        if not hard:
            # Sets soft domain of var to just the value assigned to var
            self.__soft_domains[var] = {assignment[var]}

            # Calls soft AC3 on just the neighbours of var
            # If result is invalid, invalidates soft_inferences

            # Calculates inferences for soft_domains if result soft AC3 is valid
            if self.AC3(queue=[(Y, var) for Y in neighbours], hard=False):
                for node in self.__soft_domains:
                    if len(self.__soft_domains[node]) == 1 and assignment[node] is None:
                        inferences[node] = list(self.__soft_domains[node])[0]
        else:
            self.__hard_domains[var] = {assignment[var]}
            # Calls hard AC3 on just the neighbours of var 
            # If result is invalid, return None
            '''
            if (problem_var := self.AC3(queue=[(Y, var) for Y in neighbours])) is not None:
                return problem_var
            '''
            if not self.AC3(queue=[(Y, var) for Y in neighbours]):
                return None

            # Calculates inferences for hard_domains 
            for node in self.__hard_domains:
                if len(self.__hard_domains[node]) == 1 and assignment[node] is None:
                    inferences[node] = list(self.__hard_domains[node])[0]

        return inferences
    
    def backtrack(self, assignment:dict, constructors:list):
        """
        Modified backtracking algorithm for solving constraint satisfaction
        problem with multiple resources

        Args:
            assignment (dict): current assignment of values to variables
            constructors (list[function]): list of functions that, when called, construct a ConstraintGraph object for a particular resource allocation problem

        Raises:
            NoSolution: no solution exists

        Returns:
            list[dict] | None: returns solution if found else None if dead end reached
        """
        
        # BASE CASE
        
        if self.complete(assignment):
            
            # If the current ConstraintGraph object is the last,
            # no more recursion needed -> returns full solution
            if constructors == []:
                return StructTools.deepCopy(self.__solution) + [assignment]
            else:
                # Gets next ConstraintGraph object
                next = constructors[0](self.__solution + [assignment] if self.__solution is not None else [assignment])
                # Calls its solve method and returns result of that
                try:
                    return next.solve(constructors[1:])
                #except NoSolution as e:
                    #return e.problem_var
                except NoSolution:
                    return None
        
        # Gets next unassigned variable
        var = self.selectUnassignedVar(assignment)
        #sub_layer_problem_var = None

        #print(var)
        
        # Gets domain of current var (ordered based on heuristic)
        domain_vals = self.domainVals(var, assignment)
        
        # If its domain is empty, then dead end reached
        if domain_vals == []:
            return None
        
        # Iterates over domain
        for (val, soft) in domain_vals:
            # If the current val is inconsistent with current assignment, skip
            assignment_cp = assignment.copy()
            assignment_cp[var] = val
            if self.consistent(assignment_cp):
                # Assign val to var
                assignment[var] = val
                
                # Creates copy of hard_ and soft_domains
                hard_domains_cp = StructTools.deepCopy(self.__hard_domains)
                soft_domains_cp = StructTools.deepCopy(self.__soft_domains)
                
                # Only need to get and enforce new soft unary constraints (due to updated assignment)
                # when we are considering the soft domain
                if soft:
                    self.makeNodeConsistent(assignment, hard=False)
                
                # Gets inferences
                inferences = self.inference(assignment, var, soft)
                
                # If inferences is invalid, we are looking at the hard domains and there aren't any hard unary constraints,
                # then there is no solution
                if inferences is None:
                    raise NoSolution
                else:
                    assignment.update(inferences)
                    result = self.backtrack(assignment, constructors)
                    
                    if result is not None:
                        return result      
                # Reaches this point if either inferences is empty but there are hard unary constraints, or
                # all possible further assignments are dead ends
                
                # Resets assignment and domains
                assignment = assignment_cp
                assignment[var] = None
                self.__hard_domains = hard_domains_cp
                self.__soft_domains = soft_domains_cp

        # Dead end, so returns none
        #return sub_layer_problem_var
        return None
    
    def complete(self, assignment: dict):
        """
        Checks if assignment is complete

        Args:
            assignment (dict): Current assignment of values to variables

        Returns:
            bool: Whether assignment is complete or not
        """
        # If there are any entries that are None, then assignment is incomplete -> Return False
        for var in assignment:
            if assignment[var] is None:
                return False

        # Else, it is complete -> Returns True
        return True
    
    def selectUnassignedVar(self, assignment: dict, hard=True):
        """
        Chooses an unassigned variable based on the Minimum Remaining Values
        heuristic

        Args:
            assignment (dict): Current assignment of values to variables
            soft (bool, optional): Indicates whether to consider soft or hard constraints. Defaults to True.

        Raises:
            ValueError: Raised when the assignment is already complete or when all the domaisn are empty.

        Returns:
            str: Variable name
        """
        # Gets list of all unassigned variables
        var_list = []
        for var in assignment:
            if assignment[var] is None:
                var_list.append(var)
        
        # Raises ValueError if assignment is already complete
        if len(var_list) == 0:
            raise ValueError("Assignment is complete")
        
        # Finds min by comparing length of domains (either soft or hard depending on the 'soft' argument)
        min_key = lambda x: len(self.__soft_domains[x]) if not hard else len(self.__hard_domains[x])
        
        # If the soft domains of all the variables in var_list are empty,
        # then select a variable based on hard_domains
        if False not in [min_key(var) == 0 for var in var_list]:
            if not hard:
                return self.selectUnassignedVar(assignment, True)
            else:
                raise ValueError("All domains are empty")
        
        # Initialises list that tracks all the variables with minimum length
        mins = []
        
        # Keeps looping until all min variables of equal length are found
        all_found = False

        while not all_found:
            # Gets current min var out of var_list
            curr_min = min(var_list, key=min_key)
            # Adds it to mins list
            mins.append(curr_min)
            # Removes it from var_list
            var_list.remove(curr_min)
            
            # If var_list is empty, then all min variables have been found
            if len(var_list) > 0:
                # Otherwise, if length of curr_min's domain is not equal to the min in 
                # the updated var_list, then all have been found
                all_found = min_key(curr_min) != min_key(min(var_list, key=min_key))
            else:
                all_found = True
        
        # If there is only one element in mins, return that element
        if len(mins) == 1:
            return mins[0]
        
        # Otherwise, return the variable out of mins with the most neighbours
        return max(mins, key=lambda x: len(self.neighbours(x)))

    def domainVals(self, var, assignment:dict):
        """
        Gets list of values in domain of var ordered by the customised
        domain ordering function, followed by a modified version
        of the Arc Degree heuristic

        Args:
            var (variable): Variable being assigned to
            assignment (dict): Current assignment of values to variables

        Returns:
            list: sorted list of values in domain
        """
        # cust_ord_domain : Ordered hard domain
        # cust_ord_soft_domain : Ordered soft domain
        # equal_vals_hard, equal_vals_soft : 
        #    Tuples of consecutive values from each ordered
        #    hard or soft domains that have equal priority
        cust_ord_hard_domain, cust_ord_soft_domain, equal_vals_hard, equal_vals_soft = self.__custom_domain_vals(StructTools.deepCopy(assignment), StructTools.deepCopy(self.__hard_domains[var]), StructTools.deepCopy(self.__soft_domains[var]), var)

        # Orders the equal_vals using Arc Degree,
        # replaces them in the domains and joins the
        # ordered hard and soft domains together
        return self.completeDomainOrdering(cust_ord_soft_domain, equal_vals_soft, var, assignment, False) + self.completeDomainOrdering(cust_ord_hard_domain, equal_vals_hard, var, assignment, True)
        
    def completeDomainOrdering(self, curr_domain, unordered_vals, var, assignment, hard):
        """
        Orders any streaks of values that are equal from
        the inputted domain using Arc Degree, then replace-inserts
        them into the ordered domain

        Args:
            curr_domain (list): The current ordered domain
            unordered_vals (list[tuple]): List of tuples which hold streaks of equal vals
            var (str): The string representation of the variable
            assignment (dict[list]): The current assignment of vals to vars
            hard (bool): Flag indicating whether the domain is hard or soft

        Returns:
            list[tuple]: List of pairs containing the value and whether it's taken from
                         the hard or soft domain
        """        
        domains = {"hard" : self.__hard_domains, "soft" : self.__soft_domains}
        # Gets neighbours of var
        neighbours = self.neighbours(var)
        
        # Removes nodes from neighbours list if they have been assigned values
        to_remove = []
        for neighbour in neighbours:
            if assignment[neighbour] is not None:
                to_remove.append(neighbour)
        
        for node in to_remove:
            neighbours.remove(node)
        
        # Orders each group of adjacent unordered vals and 
        # inserts them into domain
        for group in unordered_vals:
            start_index = curr_domain.index(group[0])
            end_index = curr_domain.index(group[-1])
                
            ordered_group = StructTools.quickSort(list(group), key=lambda x: sum([self.isConflict(x, domain=domains["hard" if hard else "soft"][neighbour]) for neighbour in neighbours]))
            
            curr_domain[start_index : end_index + 1] = ordered_group
        
        # Replaces each val with a tuple storing the val and a flag indicating
        # whether this val is taken from the hard or soft domain
        return [(x, not hard) for x in curr_domain]
    
    def isConflict(self, val, other=None, domain=None):
        """
        Detects whether there is a conflict between either
        two values or a value and a domain
        Supports values of tuple type

        Args:
            val (single or tuple): The main value operand
            other (single or tuple, optional): Represents the other value operand. Defaults to None.
            domain (_type_, optional): Represents a domain operand. Defaults to None.

        Returns:
            bool: Whether there is a conflict or not
        """
        if not (other is None or domain is None):
            raise Exception("Can't give values to both 'other' and 'domain'")
        
        # If the val operand is a tuple, the logic is different
        # to when it is a single type (e.g. int or str)
        
        if type(val) is tuple:
            # If the other operand is a single tuple,
            # check if no elements in val are in other
            if other is not None:
                return set(val) & set(other) != set()
            # If the other operand is a domain, check there are no overlaps
            # between every tuple in the domain and val
            else:
                for other_val in domain:
                    if set(val) & set(other_val) != set():
                        return True
                
                return False
        else:
            # If the other operand is a single type,
            # check equality
            if other is not None:
                return val == other
            # Otherwise, check if val is in domain
            else:
                return val in domain
        
    def consistent(self, assignment: dict):
        """
        Checks if assignment is valid

        Args:
            assignment (dict): Current assignment of values to variables

        Returns:
            bool: Indicates validity of current assignment
        """
        # If there is an arc on the conflict graph such that both variables in arc are assigned to
        # and they both have the same value, then assignment is invalid
        for (X, Y) in self.__conflicts:
            if not (assignment[X] is None or assignment[Y] is None) and self.isConflict(assignment[X], other=assignment[Y]):
                return False
            
        # Otherwise, pass the current assignment through the plugin consistency check function (if it exists)
        if self.__custom_consist_check is None:
            return True
        else:
            return self.__custom_consist_check(assignment)

    def solve(self, constructors: list):
        """
        Solves this object's Constraint Satisfaction Problem
        
        Args:
            constructors (list[function]): List of functions that construct ConstraintGraphs for remaining resources to be allocated

        Raises:
            NoSolution: Raised if no solution exists

        Returns:
            solution: Solution containing assignments of all resources below it (including the current assignment)
        """
        
        # Checks node consistency for hard domains
        self.makeNodeConsistent()
        
        # Sets soft_domains to be the same as hard_domains
        self.__soft_domains = StructTools.deepCopy(self.__hard_domains)
        
        # Calls AC3 algorithm, catching NoSolution error
        if not self.AC3():
            raise NoSolution
        # Calls backtrack method, starting with empty assignment
        return self.backtrack({var : None for var in self.__variables}, constructors)

def generate(constructors: list):
    """
    Generates solution for all resources

    Args:
        constructors (list[function]): List of functions that construct ConstraintGraphs for remaining resources to be allocated

    Returns:
        list[dict]: Full solution containing assignments for all resources
    """
    try:
        return constructors[0]().solve(constructors[1:])
    except NoSolution:
        raise SystemExit("The inputted timetabling problem has no feasible solution")

class NoSolution(Exception):
    """
    Exception raised when there is no solution to the current graph
    """   
    ''' 
    def __init__(self, problem_var):
        self.problem_var = problem_var
        super().__init__()
    '''
    pass