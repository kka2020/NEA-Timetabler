import StructTools

class ConstraintSystem():
    """
    Generates and stores the data attributes to be passed into the ConstraintGraph objects
    Also stores custom consistency-check functions (references to which are passed into
    the ConstraintGraph objects)
    """    
    def __init__(self, spec, import_mode=False):
        """
        Constructor

        Args:
            spec (UserSpec): Object holding user input data
            import_mode (bool, optional): Indicates whether we are importing the class in order to
            use a specific method (i.e. in checkFeasibility) or not. Defaults to False.
        """        
        self.__spec = spec
        
        if not import_mode:
            self.__session_vars = self.getSessionVars()
            
            
            self.__session_domain = set(range(self.__spec.periods * self.__spec.days))

            mod_sub = self.transpose(self.__spec.course_to_modules)
            # Extracts the module from the session's string identifier
            get_mod = lambda var: int(var[4] if var[5] == "," else var[4:6])
            self.__conflicts = {var : mod_sub[get_mod(var)] for var in self.session_vars}

            self.__room_domains = {var : domain for (var, domain) in self.getRoomDomains()}

    @property
    def session_vars(self):
        return self.__session_vars
    
    @property
    def session_domain(self):
        return self.__session_domain
    
    @property
    def conflicts(self):
        return self.__conflicts
    
    @property
    def room_domains(self):
        return self.__room_domains
    
    def getSessionVars(self):
        """
        Generates list of session string identifiers

        Returns:
            list: List of session string identifiers
        """        
        session_vars = []
        
        for m in range(self.__spec.module_count):
            for session in ["lec", "sem", "lab"]:
                for i in range(self.__spec.session_counts[session][m]):
                    session_vars.append(f"{session}({m},{i})")
        
        return session_vars
       
    def transpose(self, inp_dict):
        """
        Flips axes of dictionary (values become keys and keys become values)
        Many-to-one mappings in original become one-to-many, which are dealt with by making each
        entry a list of values (in the transposed dict)

        Args:
            inp_dict (dict): Original dictionary

        Returns:
            Dict[List]: Tranposed dictionary of lists
        """        
        output = dict()

        for (key, values) in inp_dict.items():
            for val in values:
                if val in output.keys():
                    output[val].append(key)
                else:
                    output[val] = [key]
        
        return output
    
    def getRoomDomains(self):
        """
        Generates the room domains for each session (with unary constraints built-in).
        Each value within each domain is a tuple representing the possible rooms that can 
        be used to host the session.

        Yields:
            dict[set[tuple]]: Dictionary mapping session identifier to its room domain
        """     
        # Maps each module to the courses that take it   
        mod_to_courses = self.transpose(self.__spec.course_to_modules)

        # Maps a unique group of courses to the modules that they all share
        unique_course_sub = dict()
        for mod in range(self.__spec.module_count):
            if tuple(mod_to_courses[mod]) not in unique_course_sub.keys():
                unique_course_sub[tuple(mod_to_courses[mod])] = [mod]
            else:
                unique_course_sub[tuple(mod_to_courses[mod])].append(mod)
        
        for (courses, mod_group) in unique_course_sub.items():
            # Total number of students in this course group
            num_taking = sum((self.__spec.course_student_counts[course] for course in courses))
            
            # Each module can have lec, sem and lab sessions
            for session_type in ["lec", "sem", "lab"]:
                # Gets all the rooms that are compatible with session_type (unary constraint)
                # I.E lec_sess -> lec_room or sem_room, sem_sess -> sem_room, lab_sess -> lab_room
                valid_rooms = set(self.__spec.rooms[session_type]) | (set(self.__spec.rooms["sem"]) if session_type == "lec" else set())

                # Gets all valid room combs (based on capacity) and converts it into
                # formatted domain
                domain = self.searchRoomCombs(valid_rooms, num_taking)
                domain = {tuple(path) for path in domain}
                
                # Removes selections that have same rooms (i.e. differently ordered duplicates)
                to_remove = set()
                for x in domain:
                    for y in domain:
                        if x == y or y in to_remove:
                            continue
                        
                        if set(x) == set(y):
                            to_remove.add(x)
                
                domain -= to_remove
                
                # Duplicates domain the number of times this session occurs per week 
                # (as according to session_counts)
                for mod in mod_group:
                    for i in range(self.__spec.session_counts[session_type][mod]):
                        yield (f"{session_type}({mod},{i})", domain)
            
    def searchRoomCombs(self, rooms_left, num_taking, curr_list=[]):
        """
        Gets all the possible combinations of rooms that can host
        a given session, constrained such that the total capacity must exceed the
        num_taking

        Args:
            rooms_left (set): Set containing the remaining rooms available
            num_taking (int): Total number of students taking this module
            curr_list (list, optional): The current room combination we are computing. Defaults to [].

        Returns:
            list[list]: List containing possible room combinations
        """

        # BASE STATE

        # If the capacity is equal to or exceeds the number of students then
        # the room combination is complete and we can return it
        if sum((self.__spec.capacities[room] for room in curr_list)) >= num_taking:
            return [curr_list]
        elif len(rooms_left) == 0:
            return []
        
        output = []

        # Recursively calls itself for every room in rooms_left
        for room in rooms_left:
            next_rooms = rooms_left - {room}
            output += self.searchRoomCombs(next_rooms, num_taking, curr_list + [room])
        
        return output
    
    def getLecturerDomains(self, room_assignment):
        """
        Generates lecturer domains for each session.
        Each value in each domain is a tuple of length equal to the room selection for that session

        Args:
            room_assignment (dict): The room assignment

        Returns:
            dict[set[tuple]]: Dict mapping each session identify to its lecturer domain
        """        
        domains = {var : set() for var in room_assignment}

        for var in domains:
            room_count = len(room_assignment[var])

            domains[var] = {lecturer_comb for lecturer_comb in StructTools.combinations(self.__spec.module_to_lecturers[int((var[4] if var[5] == "," else var[4:6]))], room_count)}
        
        return domains

    def lecAndRoomCustConsist(self, period_assignment):
        """
        Custom plugin consistency check (for period assignment).
        Checks that for each period there are enough rooms and lecturers to run each session
        in that period.

        Args:
            period_assignment (dict): Assignment of periods to sessions

        Returns:
            bool: Represents whether the assignment is consistent
        """        

        # Finds sessions that occur at the same time
        conflicts = []

        for X in period_assignment:
            for Y in period_assignment:
                if X == Y:
                    continue

                if not (period_assignment[X] is None or period_assignment[Y] is None) and period_assignment[X] == period_assignment[Y]:                    
                    conflicts.append((X, Y))
        
        # For every pair of sessions that temporally confilct,
        # removes any values from the first domain that share rooms with every other value
        # in the other domain.
        room_domains = dict()
        for (X, Y) in conflicts:
            room_domains.update({X : self.room_domains[X], Y : self.room_domains[Y]})

            to_remove = set()
            for x in room_domains[X]:
                for y in room_domains[Y]:
                    if set(x) & set(y) == set():
                        break
                else:
                    to_remove.add(x)
            
            room_domains[X] -= to_remove

            # If any room domain is empty, then the current period assignment isn't consistent
            if len(room_domains[X]) == 0:
                return False
        
        # Dictionary mapping each session to the minimum number of rooms that occur in a room selection in that session's room domain
        # We use these to generates lecturer domains since these values have the lowest chance of colliding with each other
        min_room_counts = {v : len(min(room_domains[v], key=len)) for v in room_domains}

        # Dict mapping each session to its lecturer domain, which is constructed using the session's min_room_count
        lec_domains = {v : {lecturer_comb for lecturer_comb in StructTools.combinations(self.__spec.module_to_lecturers[int((v[4] if v[5] == "," else v[4:6]))], min_room_counts[v])} for v in min_room_counts}

        # For every pair of sessions that temporally confilct,
        # removes any values from the first domain that share lecturers with every other value
        # in the other domain.
        for (X, Y) in conflicts:
            to_remove = set()
            for x in lec_domains[X]:
                for y in lec_domains[Y]:
                    if set(x) & set(y) == set():
                        break
                else:
                    to_remove.add(x)
            
            lec_domains[X] -= to_remove

            # If any lecturer domain is empty, then the current period assignment isn't consistent
            if len(lec_domains[X]) == 0:
                return False
        
        # If we haven't returned False already, then the assignment is consistent
        return True
        
    def lecConsist(self, period_assignment, room_assignment):
        """
        Custom plugin consistency check (for room assignment).
        Checks that for each period there are enough rooms and lecturers to run each session
        in that period.

        Args:
            period_assignment (dict): Assignment of periods to sessions (taken from previous solution)
            room_assignment (dict): Current assignment of room selections to sessions

        Returns:
            bool: Represents whether the assignment is consistent
        """
        # Finds sessions that occur at the same time
        conflicts = []

        for X in period_assignment:
            for Y in period_assignment:
                if X == Y:
                    continue

                if period_assignment[X] == period_assignment[Y]:                    
                    conflicts.append((X, Y))
        
        # Gets the number of rooms used by each session
        room_counts = dict()
        for var in room_assignment:
            if room_assignment[var] is None:
                continue
            
            room_counts[var] = len(room_assignment[var])
        
        # Dict mapping each session to its lecturer domain, which is constructed using the session's room selection
        lec_domains = {v : {lecturer_comb for lecturer_comb in StructTools.combinations(self.__spec.module_to_lecturers[int((v[4] if v[5] == "," else v[4:6]))], room_counts[v])} for v in room_counts}

        # For every pair of sessions that temporally confilct,
        # removes any values from the first domain that share lecturers with every other value
        # in the other domain.
        for (X, Y) in conflicts:
            if not (X in lec_domains and Y in lec_domains):
                continue

            to_remove = set()
            for x in lec_domains[X]:
                for y in lec_domains[Y]:
                    if set(x) & set(y) == set():
                        break
                else:
                    to_remove.add(x)
            
            lec_domains[X] -= to_remove
            
            # If any lecturer domain is empty, then the current room assignment isn't consistent
            if len(lec_domains[X]) == 0:
                return False
        
        # If we haven't returned False already, then the assignment is consistent
        return True