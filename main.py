import pandas as pd
import os
from itertools import combinations
import sys
from datetime import datetime

"""
Basic functions
"""
def preprocessing(file_studentprefs, file_constraints):
    nb_path = os.path.abspath("main.py")

    # read student preference file
    s_pref_path = os.path.join(os.path.dirname(nb_path), file_studentprefs)
    s_pref_file = open(s_pref_path, "r")
    num_s = int(s_pref_file.readline()[8:])  # number of students
    s_pref = []  # 2D array with student id integer (index) and preferences (value), index 0 is first student
    perfect_score = 0
    for line in s_pref_file:
        values = line.split()
        perfect_score = perfect_score+len(values)-1
        x = [int(i) for i in values[1:5]]
        s_pref.append(x)

    # read constraints file
    constraints_path = os.path.join(os.path.dirname(nb_path), file_constraints)
    constraints_file = open(constraints_path, "r")
    num_t = int(constraints_file.readline()[12:])  # number of timeslots
    num_r = int(constraints_file.readline()[5:])  # number of rooms
    roomSize = []  # 2D array with room (index) and room number and size(value), first room room is index 0 and value[0] 1
    for num in range(0, num_r):
        x = constraints_file.readline()
        words = x.split()
        roomSize.append([num + 1, int(words[1])])
    num_c = int(constraints_file.readline()[8:])  # number of classes
    num_p = int(constraints_file.readline()[8:])  # number of professors
    profsClasses = []  # array with class (index) and professor (value), index 0 is class 1 and professor
    for num in range(0, num_c):
        line = constraints_file.readline()
        words = line.split()
        profsClasses.append(words[1])

    # student preference conflicts
    class_popularity = [0 for i in range(0, num_c)] #array with class (index) and popularity score(value), index 0 is class 1
    conflict = dict() #dict with string class pair (key) and priority score (value)
    weight = 1
    for classList in s_pref:
        for classes in classList:
            class_popularity[classes - 1] = class_popularity[classes - 1] + 1
            # increase popularity if class appears
        combo = combinations(classList, 2)
        for pair in combo:
            class1 = pair[0]
            class2 = pair[1]
            keya = str(class1) + ', ' + str(class2)
            keyb = str(class2) + ', ' + str(class1)  # check both variations of class combinations
            if keya in conflict:
                conflict[keya] = conflict[keya] + weight
            elif keyb in conflict:
                conflict[keyb] = conflict[keyb] + weight
            else:
                conflict[keya] = weight  # pair is not in conflict, add
            # adjust weights for each class pairing based on how many times they show up in student preferences together
    conflict = sorted(conflict.items(), key=lambda x: x[1], reverse=True)
    return num_t, num_r, num_c, num_s, class_popularity, profsClasses, roomSize, conflict, s_pref, perfect_score

def timeForClass(conflict, profsClasses, num_t, num_r, num_c):
    visited = [False for i in range(num_c)] # array with class number (index) and boolean (value), index of 0 is class 1
    timeSlots = [[] for i in range(num_t)] # 2D array with timeslot (index) and list of classes (value), index of 0 is timeslot 1
    #first in the slot_availability array is the most available timeslot
    slot_availability = [[i+1, num_r] for i in range(num_t)] #2d array wih value[0] is timeslot starting at 1, value[1] is rooms still available
    class_times = [0 for i in range(num_c)] # array with class (index) and class time (value), index of 0 is class 1
    for pair, score in conflict:
        pair = pair.split(", ")
        class1 = int(pair[0])
        class2 = int(pair[1])
        # get their pair in prof's list (cannot be at same time)
        paired1 = sameProf(profsClasses, class1)
        paired2 = sameProf(profsClasses, class2)

        if (visited[class1-1] == False):  # if first class has not been visited, check in slots and try to add
            for slot in slot_availability:
                if (slot[1]>0 and paired1 not in timeSlots[slot[0]-1]):
                    # if slot not filled and prof's other class not in slot, add
                    if not timeSlots[slot[0]-1]:
                        timeSlots[slot[0]-1] = [class1]
                        class_times[class1-1] = slot[0]
                        visited[class1-1] = True
                        slot[1] = slot[1]-1
                        break
                    else:
                        timeSlots[slot[0]-1].append(class1)
                        class_times[class1-1] = slot[0]
                        visited[class1-1] = True
                        slot[1] = slot[1]-1
                        break
            slot_availability = sorted(slot_availability, key=lambda x: x[1], reverse=True)
        if (visited[class2-1] == False):  # if second class has not been visited, check in slots and try to add
            for slot in slot_availability:
                if (slot[1]>0 and paired2 not in timeSlots[slot[0]-1]):
                    if (class1 not in timeSlots[slot[0]-1]):
                        # if slot not filled, prof's other class or class1 not in slot, add
                        if not timeSlots[slot[0]-1]:
                            timeSlots[slot[0]-1] = [class2]
                            class_times[class2-1] = slot[0]
                            visited[class2-1] = True
                            slot[1] = slot[1]-1
                            break
                        else:
                            timeSlots[slot[0]-1].append(class2)
                            class_times[class2-1] = slot[0]
                            visited[class2-1] = True
                            slot[1] = slot[1]-1
                            break
                    elif (slot[0] == num_t):
                        # if last slot, it's okay if class2 conflicts with class1
                        timeSlots[slot[0]-1].append(class2)
                        class_times[class2-1] = slot[0]
                        visited[class2-1] = True
                        slot[1] = slot[1]-1
                        break
            slot_availability = sorted(slot_availability, key=lambda x: x[1], reverse=True)
    return (timeSlots, class_times)


def sameProf(profsClasses, classId):
    # given a class, return prof's other class
    prof = profsClasses[classId - 1]
    for i in range(0, num_c):
        if (profsClasses[i] == prof) and ((i + 1) != classId):
            return (i + 1)

def roomForClass(class_popularity, timeSlots, roomSize, num_r, num_c):
    classrooms = [] # 2D array with index=class starting at 0, value[0]=class starting at 1, value[1]=room starting at 1
    roomSize = sorted(roomSize, key=lambda x: x[1], reverse=True)
    # 2D array with room (index) and room number and size(value), first room is index 0
    for slot in timeSlots:
        classes_in_slot = []
        for c in slot:
            classes_in_slot.append([c, class_popularity[c - 1]])
        classes_in_slot = sorted(classes_in_slot, key=lambda x: x[1], reverse=True)
        # for each time slot, sort classes based on popularity (priority)
        for i in range(0, len(slot)):
            curr_class = classes_in_slot[i]
            curr_room = roomSize[i]
            classrooms.append([curr_class[0], curr_room[0]])
            # assigns classrooms based on popularity (most popular gets largest room)
    classrooms = sorted(classrooms, key=lambda x: x[0])
    return (classrooms)


def studentsForClass(classrooms, timeSlots, class_times, s_pref, num_s, num_c):
    # takes already assigned times and rooms and assigns students
    score = 0
    registration = [[] for i in range(0, num_c)]  # index is class, value is array of students, index 0 is class 1
    for i in range(0, num_s):
        registered_times = []
        for c in s_pref[i]:
            room = classrooms[c-1][1]
            class_size = (roomSize[room - 1])[1]
            class_time = class_times[c - 1]
            if len(registration[c - 1]) < class_size and class_time not in registered_times:
                # if more space in classroom and class fits in student's schedule, register them
                registration[c - 1].append(i + 1)
                registered_times.append(class_time)
                score = score + 1
                # increments score every time a student is registered for a class
    return registration, score

def schedule(num_c, registration, classrooms, profsClasses, class_times, file_schedule):
    # takes in all assignments and prints out in new txt file
    orig_stdout = sys.stdout
    sys.stdout = open(file_schedule, "w")
    print("Course\tRoom\tTeacher\tTime\tStudents")
    for i in range(0, num_c):
        students = " ".join(str(item) for item in registration[i])
        print("%d\t%d\t%d\t%d\t%s" % (
            i + 1, int((classrooms[i])[1]), int(profsClasses[i]), int(class_times[i]), students))
    sys.stdout.close()
    sys.stdout = orig_stdout



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: " + sys.argv[0] + " <student_prefs.txt> <constraints.txt> <schedule.txt>")
        exit(1)

    #Basic test
    start = datetime.now()
    num_t, num_r, num_c, num_s, class_popularity, profsClasses, roomSize, conflict, s_pref, perfScore = preprocessing(sys.argv[1], sys.argv[2])
    timeSlots, class_times = timeForClass(conflict, profsClasses, num_t, num_r, num_c)
    classrooms = roomForClass(class_popularity, timeSlots, roomSize, num_r, num_c)
    registration, score = studentsForClass(classrooms, timeSlots, class_times, s_pref, num_s, num_c)
    schedule(num_c, registration, classrooms, profsClasses, class_times, sys.argv[3])
    print("Basic Test")
    print("Student Preference Value: ", score)
    print("Best Case Student Value: ", perfScore)
    print("Fit Score: ", score / perfScore)
    print("Runtime: ", datetime.now() - start)
