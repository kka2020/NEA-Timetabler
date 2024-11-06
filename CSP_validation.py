from StructTools import chain

def formatTimetable(solution):
    """
    Formats solution structure into a dict mapping each period to a list of 
    lists representing the sessions that take place then. Each holds the session
    string identifier, a tuple of the rooms where it takes place in, and a tuple of lecturers
    teaching it (index in list corresponds to index of room they're teaching in).

    Args:
        solution (list[dict]): Unformatted solution

    Returns:
        dict: Formatted timetable
    """
    timetable = dict()
    
    # Iterates through each session
    for session in solution[0]:
        # Gets rooms and lecturers (for this session)
        lecturers = solution[1][session]
        rooms = solution[2][session]
        
        # Creates new entry in timetable dict if it doesn't exist for this session's period,
        # otherwise it just appends its information to the existing period entry
        if solution[0][session] not in timetable.keys():
            timetable[solution[0][session]] = [[session, lecturers, rooms]]
        else:
            timetable[solution[0][session]] = timetable[solution[0][session]].copy() + [[session, lecturers, rooms]]
    
    return timetable

def getCourseToRoom(timetable, spec):
    """
    Distributes each course's students across the available rooms for each period in the week
    and generates a dict indicating where the students for each course are at any given time.

    Args:
        timetable (dict): The generated timetable
        spec (UserSpec): Holds user input

    Returns:
        dict[dict[dict]]: Maps each session to a dict mapping each course to a dict mapping rooms to the number of students
                    from that course that are in that room
    """
    # Will map each session to a dict mapping each course to where the students are during that session
    course_to_room_by_session = dict()
    
    # Iterates through each period's list of sessions
    for sessions in timetable.values():
        for session in sessions:
            # Extracts module from session string indentifier
            mod = int(session[0][4:6] if session[0][5] != "," else session[0][4])
            
            # Gets the courses that are taught in the session
            courses = []
            
            for course in spec.courses:
                if mod in spec.course_to_modules[course]:
                    courses.append(course)
            
            # Adds entry to output dict, which holds a dict mapping each course to a blank dict
            # This blank dict will indicate where a certain number of students from the course need to be
            course_to_room_by_session[session[0]] = {course : dict() for course in courses}
            
            # Gets the rooms used for this session
            rooms = session[1]
            
            '''
            Distributes each course's students across the available rooms
            
            Fills each room with students from a course until either all the students for the course have been allocated 
            (-> Increment to next course), the room's capacity has been filled (-> Increment to next room), or both the course
            and the room have been used up (-> Increment both).
            
            When either all the courses have been allocated or all the rooms' capacity have been filled, end loop
            '''
            
            # Since we need to iterate through two iterables simultaneously in an unorthodox fashion,
            # we have to manually used the iterators
            
            # Instantiates loop condition and iterators
            complete = False
            courses_iter = iter(courses)
            rooms_iter = iter(rooms)
            
            # Instantiates loop variables
            curr_course = next(courses_iter)
            curr_room = next(rooms_iter)
            remaining_capacity = spec.capacities[curr_room]
            remaining_student_count = spec.course_student_counts[curr_course]
            
            while not complete:
                try:
                    # If we have fewer students to allocate than there is remaining capacity, allocate them all
                    # to the current room, decrement current room capacity and go to next courses
                    if remaining_student_count < remaining_capacity:
                        course_to_room_by_session[session[0]][curr_course][curr_room] = remaining_student_count
                        remaining_capacity -= remaining_student_count
                        curr_course = next(courses_iter)
                        remaining_student_count = spec.course_student_counts[curr_course]
                    # If we have more students, then fill up room, decrement current student count and go to next room
                    elif remaining_student_count > remaining_capacity:
                        course_to_room_by_session[session[0]][curr_course][curr_room] = remaining_capacity
                        remaining_student_count -= remaining_capacity
                        curr_room = next(rooms_iter)
                        remaining_capacity = spec.capacities[curr_room]
                    # If number of students left to allocate is equal to remaining capacity, then allocate all students
                    # to current room and go to next room and course
                    else:
                        course_to_room_by_session[session[0]][curr_course][curr_room] = remaining_capacity
                        curr_room = next(rooms_iter)
                        curr_course = next(courses_iter)
                        remaining_student_count = spec.course_student_counts[curr_course]
                        remaining_capacity = spec.capacities[curr_room]
                # When we have reached the end of either list, then all students have been allocated a room,
                # so we can end the loop
                except StopIteration:
                    complete = True
    
    return course_to_room_by_session
                

def validate(solution, spec):
    """
    Checks validity of a timetable solution
    Note: solution structure is in preformatting format

    Args:
        solution (list[dict]): Unformatted timetable solution
        spec (UserSpec): Holds user specification

    Returns:
        bool: Indicates validity of the solution
    """
    # Checks that every session has been assigned
    # a period, room selection and lecturer selection
    for resource in solution:
        if None in resource.values():
            return False
    
    # Will store the periods that each courses has sessions in
    course_periods = {course : [] for course in spec.course_to_modules}

    # Populates course_periods
    for session in solution[0]:
        for course in spec.course_to_modules:
            if int(session[4] if session[5] == "," else session[4:6]) not in spec.course_to_modules[course]:
                continue

            course_periods[course] += [solution[0][session]]
    
    # If any entry has duplicate periods, then a course has been timetabled to been
    # in two different sessions at the same time => The timetable is invalid
    for course in course_periods:
        if len(course_periods[course]) != len(list(set(course_periods[course]))):
            return False
    
    # Will store the periods that each room hosts sessions in
    room_periods = {room : [] for room in chain(*spec.rooms.values())}

    # Populates room_periods
    for session in solution[1]:
        # Checks if there is a lecturer for every room
        if len(solution[1][session]) != len(solution[2][session]):
            return False
        
        total_capacity = 0
        for room in solution[1][session]:
            # Populating room_periods
            room_periods[room].append(solution[0][session])
            
            # Calculates total capacity of room selection
            total_capacity += spec.capacities[room]
            
            # Checks that the session and room types are compatible
            # for all rooms in room selection
            for room_type in spec.rooms:
                if room in spec.rooms[room_type]:
                    if session[0:4] != room_type and (session[0:4] == "lec" and room_type == "lab"):
                        return False
        
        # Calculates total no. students in the session
        total_students = 0
        for course in spec.course_to_modules:
            if int(session[4] if session[5] == "," else session[4:6]) in spec.course_to_modules[course]:
                total_students += spec.course_student_counts[course]
        
        # Checks if room selection can fit all the students
        if total_students > total_capacity:
            return False
    
    # If any entry has duplicate periods, then the timetable is invalid
    # (per reasoning above)
    for room in room_periods:
        if len(room_periods[room]) != len(list(set(room_periods[room]))):
            return False

    # Will store the periods that each lecturer teaches
    lecturer_periods = [[]] * spec.lecturer_count

    # Populates lecture_periods
    for session in solution[2]:
        for lecturer in solution[2][session]:
            lecturer_periods[lecturer] = lecturer_periods[lecturer].copy() + [solution[0][session]]
    
    # If any entry has duplicate periods, then the timetable is invalid
    # (per reasoning above)
    for lecturer in lecturer_periods:
        if len(lecturer) != len(list(set(lecturer))):
            return False
    
    # If we haven't returned False, then the solution has passed all the tests
    # and is vald
    return True