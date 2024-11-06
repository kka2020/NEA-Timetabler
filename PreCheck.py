from PrepCSPInput import ConstraintSystem

def checkFeasibility(spec):
    '''
    Checks whether there are enough periods
    '''
    # Total periods in a week
    total_periods = spec.days * spec.periods
    
    for course in spec.courses:
        # If total number of sessions for the current course > total_periods, then the problem is infeasible
        if total_periods < sum(sub_session_counts[mod] for mod in spec.course_to_modules[course] for sub_session_counts in spec.session_counts.values()):
            raise SystemExit(f"ERROR: There aren't enough periods in a week to run all the sessions for course {course}")
            
    
    '''
    Checks whether there are enough rooms and lecturers
    '''
    # Checks if there are enough rooms to host each module's sessions
    for mod in range(spec.module_count):
        # Gets the number of people taking mod
        num_taking = sum(map(lambda course: spec.course_student_counts[course] if mod in spec.course_to_modules[course] else 0, spec.courses))
        
        # Gets the total available capacity for each session type and performs checks using this
        for room_type in ["lec", "sem", "lab"]:
            # If the session type is 'lec' then both seminar and lectures rooms can be used
            valid_rooms = {room for room in (spec.rooms[room_type] + (spec.rooms["sem"] if room_type == "lec" else []))}
            total_capacity = sum([spec.capacities[room] for room in valid_rooms])
            
            # If the number taking mod exceeds the total available capacity per period, then the problem is infeasible
            if total_capacity < num_taking:
                raise SystemExit(f"ERROR: number of people taking module {spec.module_names[mod]} exceeds the space capacity for sessions of type {room_type}")
            # If the smallest number of rooms required to run a particular session of mod exceeds the number of lecturers that teach mod, then
            # the problem is infeasible
            elif min(map(len, ConstraintSystem(spec, import_mode=True).searchRoomCombs(valid_rooms, num_taking))) > len(spec.module_to_lecturers[mod]):
                raise SystemExit(f"ERROR: number of {room_type} rooms required for a session for module {spec.module_names[mod]} exceeds the number of lecturers available to teach this module")