import StructTools

class SoftConstraints():
    def __init__(self, spec):
        self.spec = spec
        
    def periodSoftConstraintGen(self, assignment:dict):
        """
        Plug-in soft unary constraint function for period timetabling

        Args:
            assignment (dict): Current assignment of vals to vars

        Yields:
            tuple: A unary constraint i.e. (var, val)
        """
        # Generates when break periods are wanted by user
        if self.spec.breaks:
            yield from self.enforceBreaks(assignment)
    
    def enforceBreaks(self, assignment:dict):
        """
        Gets soft unary constraints for period allocation
        Ensures that a course doesn't have more than 3 timetabled sessions in a row
        Generator functionality inspired from https://realpython.com/introduction-to-python-generators/

        Args:
            assignment (dict): Current assignment of values to variables

        Yields:
            tuple: Conflict pair between variable and forbidden value
        """
        # Converts assignment into timetable dict in format period : list of lessons
        # (i.e transposes assignment dict)
        timetable = self.transpose(assignment)
        
        # Sorts timetable by period (ascending)
        
        # Initialises streaks dict
        # Keeps track of how many lessons there are in a row for each course
        streaks = {course : 0 for course in self.spec.course_to_modules}

        # Enumerates timetable
        for (period, lessons) in timetable.items():
            # Checks each course for potential streak
            for course in streaks:
                if period // self.spec.periods > (period - 1) // self.spec.periods:
                    streaks[course] = 0
                # If the modules of the lessons in the current period overlap with the current course's
                # modules, increment streak counter; else, reset it to 0
                if set([int(lesson[4:6]) if lesson[5] != "," else int(lesson[4]) for lesson in lessons]) & set(self.spec.course_to_modules[course]) != {}:
                    streaks[course] += 1
                else:
                    streaks[course] = 0
                
                # If there is a streak of at least 3 and either the next period has no sessions assigned to it or
                # none of the sessions in the next period are required for the current course, then yield a unary
                # constraint for all of the currents course's unassigned sessions with period + 1
                if streaks[course] >= self.spec.max_streak and (True if period + 1 not in timetable.keys() else set([int(lesson[4:5]) if lesson[5] != ")" else int(lesson[4]) for lesson in timetable[period+1]]) & set(self.spec.course_to_modules[course]) == {}):
                    for (lesson, value) in assignment.items():
                        # Skips if this sessions has already been assigned
                        if value is not None or int(lesson[4] if lesson[5] == "," else lesson[4:6]) not in self.spec.course_to_modules[course]:
                            continue

                        yield (lesson, period+1)
                    
                    # Once the next period has been forbidden, reset streaks to 0
                    streaks[course] = 0
    
    def enforcePeriodSpreading(self, assignment, hard_domain, soft_domain, var):
        """
        Plug-in custom domain value ordering for period timetabling

        Args:
            assignment (dict): Current assignment of values to vars
            hard_domain (set): The variable's hard domain
            soft_domain (set): The variable's soft domain
            var (str): The current variable

        Returns:
            tuple[list]: The ordered domains for both hard and soft domains + any streaks of adjacent
                         equal values for each respective domain
        """
        # If the user doesn't want to spread sessions across the week, indicate that all the values in thereturned
        # ordered domains have equal priority, forcing all the values to be ordered by Arc-Degree
        if not self.spec.spread_sessions:
            return list(hard_domain), list(soft_domain), [tuple(hard_domain)], [tuple(soft_domain)]
        
        domains = {"hard" : hard_domain, "soft" : soft_domain}

        # Calculates the number of periods in each day
        # according to current assignment
        periods_per_day = [0] * self.spec.days
        
        for period in assignment.values():
            if period is None:
                continue
            
            periods_per_day[period // self.spec.periods] += 1
        
        # Orders both hard and soft domains by the number of sessions in the day that the given period value is in
        domain_lists = {dom_type : StructTools.quickSort(list(domains[dom_type]), key=lambda period: periods_per_day[period // self.spec.periods]) for dom_type in domains}
        
        # Gets any streaks of adjacent values with equal periods_per_day values
        # This is because these values are interchangeable within the ordered domain and can be
        # given order by Arc-Degree (to maximise search efficiency)
        equal_vals = self.getEqualVals(domain_lists, lambda val: periods_per_day[val // self.spec.periods])
        
        return domain_lists["hard"], domain_lists["soft"], equal_vals["hard"], equal_vals["soft"]
         
    def transpose(self, inp_dict):
        """
        Makes the values the keys and the keys the values.
        Outputs as a dictionary of lists to deal with one-to-many
        relationships

        Args:
            inp_dict (dict): The dictionary we want to transpose

        Returns:
            dict[list]: The tranposed dictionary
        """    
        transposed_dict = dict()
        
        for key in inp_dict:
            # Can only make values that aren't NoneType keys
            if inp_dict[key] is not None:
                # Checks if values in the inp_dict are single values or lists
                if type(inp_dict[key]) is not list:
                    # If val has already been made into key, we only need to append it
                    # to an existing entry
                    # Otherwise, we need to create a new entry
                    if inp_dict[key] not in transposed_dict.keys():
                        transposed_dict[inp_dict[key]] = [key]
                    else:
                        transposed_dict[inp_dict[key]].append(key)
                # Otherwise, we need to iterate through every value in the list 
                else:
                    # Same as above but with every element in the list value
                    for val in inp_dict[key]:
                        if val not in transposed_dict.keys():
                            transposed_dict[val] = [key]
                        else:
                            transposed_dict[val].append(key)
        
        # Sorts output dict by key and returns
        return {key : transposed_dict[key] for key in StructTools.quickSort(list(transposed_dict.keys()))}
    
    def enforceLecturerSharing(self, assignment, hard_domain, soft_domain, var):
        """
        Plug-in custom domain value ordering for lecturer timetabling
        Ensures that sessions are spread out between lecturers, preventing one lecturer having too much work

        Args:
            assignment (dict): Current assignment of values to vars
            hard_domain (set): The variable's hard domain
            soft_domain (set): The variable's soft domain
            var (str): The current variable

        Returns:
            tuple[list]: The ordered domains for both hard and soft domains + any streaks of adjacent
                         equal values for each respective domain
        """
        # If user doesn't require this constraint, return inputs in expected format
        if not self.spec.spread_across_lecturers:
            return list(hard_domain), list(soft_domain), [tuple(hard_domain)], [tuple(soft_domain)]
        
        domains = {"hard" : hard_domain, "soft" : soft_domain}
        
        # Calculates and stores the number of sessions each lecturer teaches in a week
        num_periods_teaching = [0] * self.spec.lecturer_count
        
        for lecturers in assignment.values():
            if lecturers is None:
                continue
            
            for lecturer in range(len(num_periods_teaching)):
                if lecturer in lecturers:
                    num_periods_teaching[lecturer] += 1
        
        # Sorts both hard and soft domains by the total number of sessions taught by each
        # lecturer in the given lecturer selection
        domain_lists = {dom_type : StructTools.quickSort(list(domains[dom_type]), key=lambda val: sum(map(lambda lec: num_periods_teaching[lec], val))) for dom_type in domains}
        
        # Gets the adjacent equal values
        equal_vals = self.getEqualVals(domain_lists, lambda val: sum(map(lambda lec: num_periods_teaching[lec], val)))
        
        return domain_lists["hard"], domain_lists["soft"], equal_vals["hard"], equal_vals["soft"]

    def roomBasedOrdering(self, assignment, hard_domain, soft_domain, var):
        """
        Plug-in custom domain value ordering for room timetabling
        Ensures that the rooms used and wasted capacity produced in a given sessions
        is minimised
        Achieved using a compound domain value ordering

        Args:
            assignment (dict): Current assignment of values to vars
            hard_domain (set): The variable's hard domain
            soft_domain (set): The variable's soft domain
            var (str): The current variable

        Returns:
            tuple[list]: The ordered domains for both hard and soft domains + any streaks of adjacent
                         equal values for each respective domain
        """
        # Returns input in expected format if user doesn't want this constraint
        if not self.spec.room_based_ordering:
            return list(hard_domain), list(soft_domain), [tuple(hard_domain)], [tuple(soft_domain)]
        
        initial_domains = {"hard" : hard_domain, "soft" : soft_domain}
        # The final ordered domains
        ordered_domains = {'hard' : None, 'soft' : None}
        # The unordered values outputted from the first ordering function
        unordered_vals = {'hard' : None, 'soft' : None}
        # The unorderd values outputted from the second ordering function
        equal_vals = {'hard' : [], 'soft' : []}
        
        # Orders domains by rooms used (1st ordering function)
        for dom_type in ["hard", "soft"]:
            ordered_domains[dom_type], unordered_vals[dom_type] = self.enforceMinRoomsUsedLocal(initial_domains[dom_type])
        
        ordered_domains, equal_vals = self.subOrder(StructTools.deepCopy(ordered_domains), unordered_vals, self.enforceMinRoomsUsedGlobal, assignment)
        ordered_domains, equal_vals = self.subOrder(StructTools.deepCopy(ordered_domains), StructTools.deepCopy(equal_vals), self.enforceMinExcessCapacity, var)
       
        return ordered_domains['hard'], ordered_domains['soft'], equal_vals['hard'], equal_vals['soft']
    
    def subOrder(self, ordered_domains, unordered_vals, ordering_func, *args):
        equal_vals = {"hard" : [], "soft" : []}
        
        # Sort unordered_vals by ordering_func and inserts
        # outputs into ordered_domains
        for dom_type in unordered_vals:
            for group in unordered_vals[dom_type]:  
                # Apply 2nd ordering function
                ordered_group, equal_group_vals = ordering_func(list(group), *args)
                
                # Insert and replace ordered_group into ordered_domains
                start_index = ordered_domains[dom_type].index(group[0])
                end_index = ordered_domains[dom_type].index(group[-1])
                ordered_domains[dom_type][start_index : end_index + 1] = ordered_group
                
                # Creates list of equal_vals
                # (i.e. streaks of adjacent unordered vals)
                for sub_group in equal_group_vals:
                    if len(sub_group) > 0:
                        equal_vals[dom_type].append(sub_group)
        
        return ordered_domains, equal_vals
    
    def enforceMinRoomsUsedGlobal(self, group, assignment):
        room_use_freq = {room : 0 for room in StructTools.chain(*self.spec.rooms.values())}
        
        for room_selection in assignment.values():
            if room_selection is None:
                continue
            
            for room in room_use_freq:
                if room in room_selection:
                    room_use_freq[room] += 1
        
        sort_key = lambda room_selec : sum([room_use_freq[room] == 0 for room in room_selec])
        ordered_group = StructTools.quickSort(list(group), key=sort_key)
        
        equal_vals = self.getEqualVals({"hard" : ordered_group}, sort_key)
        
        return ordered_group, equal_vals["hard"]
        
    def enforceMinRoomsUsedLocal(self, group):
        """
        1st ordering function in roomBasedOrdering
        Attempts to minimise the number of rooms used to run a given session
        This in turn reduces the number of lecturers required to run a given session

        Args:
            hard_domain (set): The variable's hard domain
            soft_domain (set): The variable's soft domain

        Returns:
            tuple[list]: The ordered domains for both hard and soft domains + any streaks of adjacent
                         equal values for each respective domain
        """        
        # Sorts domains by no. rooms used
        ordered_group = StructTools.quickSort(list(group), key=len)
        
        # Gets list of streaks of adjacent unordered vals
        equal_vals = self.getEqualVals({"hard" : ordered_group}, len)
        
        return ordered_group, equal_vals["hard"]
        
    def enforceMinExcessCapacity(self, group, var):
        """
        3rd ordering function in roomBasedOrdering
        Attempts to minimise the excess capacity created from running a given

        Args:
            group (tuple): Adjacent unordered vals from the 1st ordering
            var (str): String representation of the current session

        Returns:
            tuple[list]: The ordered domains group + any streaks of adjacent
                         equal values
        """
        # Extracts the current module from var
        mod = int(var[4] if var[5] == "," else var[4:6])
        
        # Gets the courses that take the module mod
        courses = self.transpose(self.spec.course_to_modules)[mod]
        
        # Function that calculates the excess capacity from a given room selection
        # by subtracting the total capacity from the number of students in the session
        excess = lambda room_selection: (sum((self.spec.capacities[room] for room in room_selection)) 
                                        - sum((self.spec.course_student_counts[course] for course in courses)))
        
        ordered_group = StructTools.quickSort(list(group), key=excess)
        
        equal_vals = self.getEqualVals({'hard' : ordered_group}, excess)
        equal_vals = equal_vals['hard']
        
        return ordered_group, equal_vals
    
    def getEqualVals(self, domain_lists, cost_func):
        equal_vals = {"hard" : [], "soft" : []}
        for dom_type in domain_lists:
            curr_equal_streak = []
            for val in domain_lists[dom_type]:
                if len(curr_equal_streak) == 0 or cost_func(curr_equal_streak[-1]) == cost_func(val):
                    curr_equal_streak.append(val)
                else:
                    equal_vals[dom_type].append(curr_equal_streak)
                    curr_equal_streak = [val]
        
            if curr_equal_streak != []:
                equal_vals[dom_type].append(curr_equal_streak)
        
        return equal_vals

    
        