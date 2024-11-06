from UserSpec import UserSpec
from CSP import ConstraintGraph, generate
from Viewer import Viewer
import CSP_validation as Validator
from SoftConstraints import SoftConstraints
from PrepCSPInput import ConstraintSystem
from PreCheck import checkFeasibility
import sys
import StructTools

if __name__ == "__main__":
    doc = ""

    # Catches command-line argument error
    try:
        in_doc = sys.argv[1]
        out_doc = sys.argv[2]
    except IndexError:
        raise SystemExit(f"Usage: {sys.argv[0]} [input-doc-name] [output-doc-name]")
    
    if len(sys.argv) > 3:
        raise SystemExit(f"Usage: {sys.argv[0]} [input-doc-name] [output-doc-name]")
    
    if out_doc[-4:] != "xlsx":
        raise SystemExit("The output document name must have a .xlsx file extension")

    # Gets all the relevant information from user input document
    print("Extracting data...")
    spec = UserSpec(in_doc)

    # Instantiates object storing all the soft constraint functions
    print("Configuring soft constraint functions...")
    soft_constraints = SoftConstraints(spec)
    
    # Gets all the variables and sets in the problem system
    print("Instantiating constraint systems...")
    constr_system = ConstraintSystem(spec)

    # Checks whether the problem is feasible (with respect to the number of students and room capacities) 
    # before any backtracking search begins
    print("Running pre-process feasibility check...")
    checkFeasibility(spec)

    # Defines the constraint satisfaction problems for each resource (periods, rooms and lecturers)
    # passing in the relevant data generated from constr_system and any custom constraints from
    # soft_constraints
    # Allows instantiation of a ConstraintGraph with particular parameters whenever required
    # by backtrack method
    constructors = [
        lambda : ConstraintGraph(
            constr_system.session_vars,
            constr_system.session_domain,
            constr_system.conflicts,
            soft_unary_constraints=soft_constraints.periodSoftConstraintGen,
            custom_domain_vals=soft_constraints.enforcePeriodSpreading,
            custom_consist_check=constr_system.lecAndRoomCustConsist
        ),
        lambda solution: ConstraintGraph(
            constr_system.session_vars,
            constr_system.room_domains,
            # Period assignment is conflict list for room assignment since sessions that occur at the same
            # time can't be assigned the same room
            {key : [solution[0][key]] for key in solution[0]}, 
            solution=solution,
            custom_domain_vals=soft_constraints.roomBasedOrdering,
            custom_consist_check=lambda room_assignment: constr_system.lecConsist(solution[0], room_assignment)
        ),
        lambda solution: ConstraintGraph(
            constr_system.session_vars,
            constr_system.getLecturerDomains(solution[1]),
            # Period assignment is conflict list for lecturer assignment as well for similar reasons as above
            {key : [solution[0][key]] for key in solution[0]},
            solution=solution,
            custom_domain_vals=soft_constraints.enforceLecturerSharing
        )
    ]
    
    print("Generating timetable...")
    # Generates timetable solution
    solution = generate(constructors)
    
    print("Validating timetable...")
    # Checks if solution is valid
    if not Validator.validate(solution, spec):
        raise Exception("Invalid solution")

    viewer = Viewer(spec)
    
    print(f"Writing timetable to {out_doc}...")
    # Formats solution into table form
    timetable = Validator.formatTimetable(solution)
    #print({period : timetable[period] for period in StructTools.quickSort(list(timetable.keys()))})
    
    # Generates timetable excel file
    viewer.viewTimetable(timetable, Validator.getCourseToRoom(timetable, spec), out_doc)
    
    print("Done!")