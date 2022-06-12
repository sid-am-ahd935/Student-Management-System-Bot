import sqlalchemy
import re
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base

base_menu = """
Choose one of the following options:

1 - Enter student grade information
2 - Print all student grade information 
3 - Print class performance statistics 
4 - Exit

Enter your choice: """

first_menu = """
Choose one of the following options:

1.1 - Enter a BIT student information
1.2 - Enter a DIT student information
1.3 - Go back to the main menu

Enter your choice: """

second_menu = """
Choose one of the following options:

2.1 - Print all student grade information ascendingly by final mark
2.2 - Print all student grade information descendingly by final mark
2.3 - Go back to the main menu

Enter your choice: """

base_choices = {
    '1' : 'option1',
    '2' : 'option2',
    '3' : 'option3',
    '4' : 'option4',
}

first_choices = {
    '1.1' : 'option11',
    '1.2' : 'option12',
    '1.3' : 'option13',
}

second_choices = {
    '2.1' : 'option21',
    '2.2' : 'option22',
    '2.3' : 'option23',
}

engine = sqlalchemy.create_engine('sqlite:///students_db.sqlite3')
Base = declarative_base()
Session = sessionmaker()
Session.configure(bind=engine)
session = Session()

class Student(Base):
    __tablename__ = "student"

    student_id = Column(String, primary_key=True)
    student_name = Column(String)
    student_name_length = Column(Integer)
    assessment_marks_1 = Column(Integer)
    assessment_marks_2 = Column(Integer)
    assessment_marks_3 = Column(Integer)
    school_type = Column(String)
    final_marks = Column(Integer)
    grade = Column(String)

    def __repr__(self):
        return f"<Student(id='{self.student_id}', name='{self.student_name}', school_type='{self.school_type}', final_marks='{self.final_marks}', grade='{self.grade}')>"


class Break(Exception):
    pass


def calcFinalMarks(student_marks):
    a, b, c = student_marks
    final_marks = 0.2 * a + 0.4 * b + 0.4 * c
    return final_marks



def saveStudent(student_id, student_name, student_marks, school_type, final_marks, grade):
    global session
    details = {
        "student_id" : student_id, 
        'student_name' : student_name, 
        'student_name_length' : len(student_name), 
        'assessment_marks_1' : student_marks[0], 
        'assessment_marks_2' : student_marks[1], 
        'assessment_marks_3' : student_marks[2], 
        'school_type' : school_type, 
        'final_marks' : final_marks, 
        'grade' : grade
    }
    # student = Student(student_id, student_name, *student_marks, school_type, final_marks, grade)
    student = Student(**details)
    session.add(student)
    session.commit()



def finalGradeBIT(student_marks : list([int,int,int])):
    ig = interim_grade = None
    sm = student_marks
    m = final_marks = calcFinalMarks(sm)


    ######## Interim Grade Letter #########

    if 85 <= m <= 100:    ig = "HD"
    elif 75 <= m < 85:    ig = "D"
    elif 65 <= m < 75:    ig = "C"
    elif 50 <= m < 65:    ig = "P"
    
    elif 45 <= m < 50:
        if sm.count(0) != 0:            #------------------------------------------------------------------------ No score marked '0'
            if sm[2] < 50:            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Exam Failed
                if sm[0] < 50 or sm[1] < 50:#======== Exam + Assessment Failed
                    ig = "F"
                else:        #======================= Only Exam Failed
                    ig = "SE"
            else:            #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Exam Passed
                if sm[0] < 50 and sm[1] < 50:        # Both Assessments Failed
                    ig = "F"
                elif sm[0] < 50 or sm[1] < 50:       # Anyone Assessment Failed
                    ig = "SA"
                else:           # All Passed
                    ig = "F"    ## This isn't supposed to come here
        else:           #---------------------------------------------------------------------------------------- Has Scored marked '0'
            ig = "F"
    
    elif 0 <= m < 45:
        if (3 >= sm.count(0) >= 2):        # Has 2 or 3 subjects scored '0'
            ig = "AF" 
        else:                   # Has One subect scored '0'
            ig = 'F'
    
    else:       ## This isn't supposed to come here
        ig = "F"


    ######### Final Grade Letter ###########

    fg = final_grade = None
    # print("final Grade", ig, "final marks", m, sm)

    if ig == "SA" or ig == "SE":
        supple_mark = int(input("What is this student's supplementary exam mark: ").strip('\n').strip())

        if ig == "SE":              # Supplementary Exam
            sm[2] = supple_mark

        elif ig == "SA":            # Supplementary Assessment
            if sm[0] < 50:
                sm[0] = supple_mark
            elif sm[1] < 50:
                sm[1] = supple_mark

        if supple_mark >= 50:   # Passed Supplementary
            fg = "SP"
        else:       # Failed Supplementary
            fg = "F"
            
        final_marks = calcFinalMarks(sm)                # Final Marks changed after giving the supplementary exam\assessment

    
    else: 
        fg = ig
    
    print("final Grade", ig, "final marks", m, sm)
    return final_marks, fg 



def finalGradeDIT(student_marks : list([int, int, int])):
    m = final_marks = calcFinalMarks(student_marks)

    if 50 <= m <= 100:
        ig = "CP"
    
    elif 0 <= m < 50:
        ig = "NYC"

    
    ####### Final Grade Letter #######

    fg = final_grade = None

    if ig == "CP":
        fg = "CP"
    
    elif ig == "NYC":
        supple_marks = None

        while not supple_marks:
            supple_marks = [mark.strip() for mark in input('What is this student’s resubmission marks (separated by comma):  ').split(',')]
            if not (len(supple_marks) == 3 and all(map(lambda x : x.isdigit(), supple_marks))):
                print('Please enter 3 subjects marks in number...')
                supple_marks = None
            else:
                supple_marks = [int(mark.strip()) for mark in supple_marks]
                break
        
        final_marks = calcFinalMarks(supple_marks)

        if 100 >= final_marks >= 50:
            fg = "CP"
        
        else:
            fg = "NC"
        
    
    return final_marks, fg
    


def takeStudentDetails():
    student_id = None
    student_name = None 
    student_marks = None 

    while not student_id:
        student_id = input("Enter student ID: ")
        if not re.match('A[0-9]{8}', student_id):
            print('Please enter a valid student Id (A capital letter "A" followed by 8 digits)...')
            student_id = None
        else:
            break
    
    student_name = input('Enter student name: ')

    while not student_marks:
        student_marks = [mark.strip() for mark in input('Enter student assessment marks (separated by comma): ').split(',')]
        if not (len(student_marks) == 3 and all(map(lambda x : x.isdigit(), student_marks))):
            print('Please enter 3 subjects marks in number...')
            student_marks = None
        else:
            student_marks = [int(mark.strip()) for mark in student_marks]
            break
    
    return student_id, student_name, *student_marks



class FirstOption:
    """
    This class has functions based on options collected from the first menu option.
    """
    def option11():
        student_id, student_name, *student_marks = takeStudentDetails()
        # print(student_marks, type(student_marks))
        final_marks, grade  = finalGradeBIT(student_marks)
        saveStudent(student_id, student_name, student_marks, "BIT", final_marks, grade)

    def option12():
        student_id, student_name, *student_marks = takeStudentDetails()
        # print(student_marks, type(student_marks))
        final_marks, grade = finalGradeDIT(student_marks)
        saveStudent(student_id, student_name, student_marks, "DIT", final_marks, grade)

    def option13():
        raise Break



class SecondOption:
    """
    This class has functions based on options collected from the second menu option.
    """
    def option21():
        global session
        query = session.query(Student).order_by(Student.final_marks.desc())
        students = query.all()
        max_name_length = session.query(Student).order_by(Student.student_name_length.desc()).first().student_name_length

        for student in students:
            print(f"{student.student_id}    {student.student_name}".ljust(max_name_length + 15) + f"{student.school_type} {student.final_marks}  {( 'F' if student.grade == 'AF' else student.grade)}")

    def option22():
        global session
        query = session.query(Student).order_by(Student.final_marks.asc())
        students = query.all()
        max_name_length = session.query(Student).order_by(Student.student_name_length.desc()).first().student_name_length

        for student in students:
            print(f"{student.student_id}    {student.student_name}".ljust(max_name_length + 15) + f"{student.school_type} {student.final_marks}  {( 'F' if student.grade == 'AF' else student.grade)}")

    def option23():
        raise Break



class ThirdChoice:
    """
    This class has functions based on options from the third base option.
    """
    def print_result():
        global session
        studentsBIT = session.query(Student).filter_by(school_type= "BIT").all()
        studentsDIT = session.query(Student).filter_by(school_type= "DIT").all()

        grade_count = {
            'HD' : 0, 
            'D' : 0, 
            'C' : 0, 
            'P' : 0,
            'SP' : 0,
            'CP' : 0,
            'AF' : 0,
            'F' : 0,
            'NC' : 0,
        }
        grade_point = {
            'HD' : 4.0, 
            'D' : 3.0, 
            'C' : 2.0, 
            'P' : 1.0,
            'SP' : 0.5,
            'CP' : 4.0,
            'AF' : 0,
            'F' : 0,
            'NC' : 0
        }
        tot_mark1 = 0
        tot_mark2 = 0
        tot_mark3 = 0
        tot_final_mark = 0
        tot_grade_points = 0
        total_students = 0

        for st in (studentsBIT + studentsDIT):
            grade_count[st.grade] += 1
            tot_mark1 += st.assessment_marks_1
            tot_mark2 += st.assessment_marks_2
            tot_mark3 += st.assessment_marks_3
            tot_final_mark += st.final_marks
            tot_grade_points += grade_point[st.grade]
            total_students += 1

        print()
        print("Number of students:", total_students)
        print("Number of BIT students", len(studentsBIT))
        print("Number of DIT students", len(studentsDIT))

        st_pass_rate = (sum(grade_count.values()) - grade_count['AF'] - grade_count['F'] - grade_count['NC']) / total_students
        print("Student Pass Rate: %0.2f" % (st_pass_rate))

        st_pass_rate_adjusted = (sum(grade_count.values()) - grade_count['AF'] - grade_count['F'] - grade_count['NC']) / (total_students - grade_count['AF'])
        print("Student Pass Rate(adjusted): %0.2f" % (st_pass_rate_adjusted))

        print("Average mark for Assessment 1: %0.2f" % (tot_mark1/total_students))
        print("Average mark for Assessment 2: %0.2f" % (tot_mark2/total_students))
        print("Average mark for Assessment 3: %0.2f" % (tot_mark3/total_students))
        print("Average final mark: %0.2f" % (tot_final_mark/total_students))
        print("Average grade point: %0.2f" % (tot_grade_points/total_students))
        for k, v in grade_count.items():
            if k not in ['AF', 'F', 'NC']:
                print(f"Number of {k}s: {v}")
        print("Number of Fs:", grade_count['F'] + grade_count['AF'] + grade_count['NC'])



class BaseMenu:
    """
    This class has functions based on options of the base or home menu.
    """ 
    def option1():
        loopSubChoices(type_= 'First')
    

    def option2():
        loopSubChoices(type_= 'Second')

    def option3():
        ThirdChoice.print_result()

    def option4():
        raise Break



def loopSubChoices(type_ : 'first or second'):
    menu = None
    choices = None
    class_ = None

    if type_ in [1, '1', 'first', 'First', 'FIRST']:
        menu = first_menu
        choices = first_choices
        class_ = FirstOption
    
    elif type_ in [2, '2', 'second', 'Second', 'SECOND']:
        menu = second_menu
        choices = second_choices
        class_ = SecondOption
    
    while True:
        try:
            choice = input(menu)
            print()
            getattr(class_, choices[choice])()
        
        except Break:
            break

        except KeyError:
            print('Please check the sub menu and choose options correctly:')
        
        except KeyboardInterrupt:
            print(" ^C")
            print("CTRL+C detected... Moving Back...")
            break



def loopBaseChoice():
    menu = base_menu
    choices = base_choices

    while True:
        try:
            choice = input(menu)
            print()
            if choice in choices:
                getattr(BaseMenu, choices[choice])()
            
            else:
                print("Please choose an option from the menu:")
        
        except Break:
            break

        except KeyboardInterrupt:
            # print("KeyboardInterrupt detected... ")
            print(" ^C")
            break



def main():
    if not sqlalchemy.inspect(engine).has_table("student"):
        Base.metadata.create_all(engine)

    loopBaseChoice()
    

if __name__ == "__main__":

    main()
    print("The program exited successfully...")
    exit(0)