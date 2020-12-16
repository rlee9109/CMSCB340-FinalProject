import pandas as pd
import os
from itertools import combinations
import sys
from datetime import datetime

"""
Extension Functions
1) Student can select more than 4 courses
2) Accounted for overlapping (non-discrete) class time slots
3) Gives some priority to introductory courses
4) Gives some priority to pairs of courses taken simultaneously by a student (likely for major requirements)
5) Gives some priority to STEM courses (STEM major requirements are stricter and require more prerequisites)
"""
def preprocessingHC(file_sprefs, file_constraints):
    nb_path = os.path.abspath("main.py")

    # read student preference file
    s_pref_path = os.path.join(os.path.dirname(nb_path), file_sprefs)
    s_pref_file = open(s_pref_path, "r")
    num_s = int(s_pref_file.readline()[8:])  # number of students
    s_pref = []  # 2D array with student id integer (index) and preferences (value), begins at 0
    studentNumbers = [] #processed student number (index) and actual id (value), begins at 0
    perfScore = 0
    for line in s_pref_file:
        values = line.split()
        studentNumbers.append(values[0])
        x = [int(i) for i in values[1:]]
        s_pref.append(x)
        perfScore = perfScore + len(values) - 1
    # read constraints file
    constraints_path = os.path.join(os.path.dirname(nb_path), file_constraints)
    constraints_file = open(constraints_path, "r")
    num_t = int(constraints_file.readline()[12:])  # number of timeslots
    timeslot_details = [] #2D array with timeslot number (index) and details (values), begins at 0
    for i in range(num_t):
        line = constraints_file.readline()
        words = line.split("\t")
        if ((words[1][0:1]) == " "):
            st = datetime.strptime(words[1]," %I:%M %p")
        else:
            st = datetime.strptime(words[1], "%I:%M %p")
        if ((words[2][0:1]) == " "):
            et = datetime.strptime(words[2]," %I:%M %p")
        else:
            et = datetime.strptime(words[2], "%I:%M %p")
        timeslot_details.append([st, et, words[3]])

    num_r = int(constraints_file.readline()[5:])  # number of rooms
    roomSize = []  # 2D array with room number ([0]) and room size ([1]), begins at 1
    roomNumbers = [] # array with room number (index) and room name (value), begins at 0
    for num in range(0, num_r):
        x = constraints_file.readline()
        values = x.split()
        roomSize.append([num + 1, int(values[1])])
        roomNumbers.append(values[0])
    num_c = int(constraints_file.readline()[8:])  # number of classes
    num_p = int(constraints_file.readline()[8:])  # number of professors
    classNumbers = dict() # dict with class name (key) and class index (value), key non consecutive not ordered, value begins at 1
    profsClasses = []  # 2D array with class number (index), and professor and class name (values), begins at 0
    for num in range(0, num_c):
        line = constraints_file.readline()
        words = line.split()
        classNumbers[int(words[0])] = num
        if(len(words) > 1):
            profsClasses.append([int(words[1]), int(words[0])])
        else:
            profsClasses.append([None,int(words[0])])
    levels = []
    subjects = []
    start_times = []
    end_times = []
    days = []
    constraints_file.readline()
    for num in range(0, num_c):
        line = constraints_file.readline()
        words = line.split('\t')
        levels.append(words[0])
        subjects.append(words[1])
        start_times.append(words[2])
        end_times.append(words[3])
        days.append(words[4])
    stem_subject = ["ASTR", "BIOL", "CHEM", "CMSC", "ECON", "ENVS", "MATH", "PHYS", "POLS", "PSYC", "SOCL", "STAT"]

    # timeslot overlap conflicts
    timeslot_overlaps = dict() # dictionary with each timeslot (key) and list of timeslot that conflict (value)
    for i in range(0, num_t):
        timeslot_overlaps[i] = []
        slotA = timeslot_details[i]
        for j in range(0, num_t):
            if i == j:
                continue
            slotB = timeslot_details[j]
            daysA = slotA[2].split()
            if ((slotA[0]<slotB[0] and slotA[1]>slotB[0])
                    or (slotB[0]<slotA[0] and slotB[1]>slotA[0])
                    or (slotA[0]<slotB[0] and slotA[1]>slotB[1])
                    or (slotB[0]<slotA[0] and slotB[1]>slotA[1]) ):
                for days in daysA:
                    if (days in slotB[2]):
                        timeslot_overlaps[i].append(j)
                        continue

    # student preference conflicts
    class_popularity = [0 for i in range(0, num_c)]
    conflict = dict() # string name pair of classes (key) and weight (value)
    for classList in s_pref:
        for classes in classList:
            # popularity count
            if(classes in classNumbers):
                classNum = classNumbers[classes]
                class_popularity[classNum] = class_popularity[classNum] + 1
        combo = combinations(classList, 2)
        # adjust weights for each class pairing based on how many times they show up in student preferences together
        for pair in combo:
            class1 = pair[0]
            class2 = pair[1]
            if (class1 in classNumbers and class2 in classNumbers):
                keya = str(class1) + ', ' + str(class2)
                keyb = str(class2) + ', ' + str(class1)  # check both variations of class combinations
                weight = 10  # add 10 weight for showing up in same combo
                if (int(levels[classNumbers[class1]]) == 1): # add 5 weight for being introductory level class
                    weight = weight+5
                if (int(levels[classNumbers[class2]]) == 1): # add 5 weight for being introductory level class
                    weight = weight+5
                if (subjects[classNumbers[class1]] == subjects[classNumbers[class2]]): # add 5 weight for pair of same subject
                    weight = weight+5
                if (subjects[classNumbers[class1]] in stem_subject): # add 1 weight for STEM subject
                    weight = weight+1
                if (subjects[classNumbers[class2]] in stem_subject): # add 1 weight for STEM subject
                    weight = weight+1
                if keya in conflict:
                    conflict[keya] = conflict[keya] + weight
                elif keyb in conflict:
                    conflict[keyb] = conflict[keyb] + weight
                else:
                    conflict[keya] = weight  # pair is not in conflict, add

    conflict = sorted(conflict.items(), key=lambda x: x[1], reverse=True)
    return num_t, num_r, num_c, num_s, class_popularity, profsClasses, roomSize, conflict, s_pref, classNumbers, roomNumbers, studentNumbers, levels, subjects,timeslot_overlaps, perfScore


def timeForClassHC(conflict, profsClasses, num_t, num_r, num_c, classNumbers, timeslot_overlaps):
    visited = [False for i in range(num_c)]
    timeSlots = [[] for i in range(num_t)]
    class_times = [0 for i in range(num_c)]
    slot_availability = [[i+1, num_r] for i in range(num_t)]
    for pair, score in conflict:
        pair = pair.split(", ")
        class1 = int(pair[0])
        class2 = int(pair[1])
        # get their pair in prof's list (cannot be at same time)
        if class1 in classNumbers:
            if (visited[classNumbers[class1]] == False):  # if first class has not been visited, check in slots and try to add
                conflict_slots = []
                paired1 = sameProfHC(profsClasses, class1, classNumbers)
                if (paired1 != None):
                    if (visited[paired1]):
                        paired_slot = class_times[paired1]-1
                        conflict_slots.append(paired_slot)
                        conflict_slots.append(x for x in timeslot_overlaps[paired_slot])
                for slot in slot_availability:
                    if (slot[1]>0 and (slot[0]-1) not in conflict_slots):
                        # if slot not filled and prof's other class not in slot, add
                        if not timeSlots[slot[0]-1]:
                            timeSlots[slot[0]-1] = [class1]
                            class_times[classNumbers[class1]] = slot[0]
                            visited[classNumbers[class1]] = True
                            slot[1] = slot[1]-1
                            break
                        else:
                            timeSlots[slot[0]-1].append(class1)
                            class_times[classNumbers[class1]] = slot[0]
                            visited[classNumbers[class1]] = True
                            slot[1] = slot[1]-1
                            break
                slot_availability = sorted(slot_availability, key=lambda x: x[1], reverse = True)
        if class2 in classNumbers:
            if (visited[classNumbers[class2]] == False):  # if second class has not been visited, check in slots and try to add
                conflict_slots = []
                paired2 = sameProfHC(profsClasses, class2, classNumbers)
                if (paired2 != None):
                    if (visited[paired2]):
                        paired_slot = class_times[paired2] - 1
                        conflict_slots.append(paired_slot)
                        conflict_slots.append(x for x in timeslot_overlaps[paired_slot])
                for slot in slot_availability:
                    if (slot[1]>0 and (slot[0]-1) not in conflict_slots):
                        if (class1 not in timeSlots[slot[0]-1]):
                            # if slot not filled, prof's other class or class1 not in slot, add
                            if not timeSlots[slot[0]-1]:
                                timeSlots[slot[0]-1] = [class2]
                                class_times[classNumbers[class2]] = slot[0]
                                visited[classNumbers[class2]] = True
                                slot[1] = slot[1]-1
                                break
                            else:
                                timeSlots[slot[0]-1].append(class2)
                                class_times[classNumbers[class2]] = slot[0]
                                visited[classNumbers[class2]] = True
                                slot[1] = slot[1]-1
                                break
                        elif (slot[0] == num_t - 1):
                            # if last slot, it's okay if class2 conflicts with class1
                            timeSlots[slot[0]-1].append(class2)
                            class_times[classNumbers[class2]] = slot[0]
                            visited[classNumbers[class2]] = True
                            slot[1] = slot[1]-1
                            break
                slot_availability = sorted(slot_availability, key=lambda x: x[1], reverse=True)
    for c in range(0,num_c): # if the class hasnt been visited, just add it to last time slot
        className = profsClasses[c][1]
        if visited[c] == False:
            timeSlots[num_t-1].append(className)
            class_times[c] = num_t
            visited[c] = True
    return (timeSlots, class_times)

def sameProfHC(profsClasses, classId, classNumbers):
    # given a class, return prof's other class
    classNum = classNumbers[classId]
    prof = profsClasses[classNum][0]
    if (prof == None):
        return None
    else:
        for i in range(0, num_c):
            if (profsClasses[i][0] != None):
                if (profsClasses[i][0] == prof) and (i != classNum):
                    return (i)

def roomForClassHC(class_popularity, timeSlots, roomSize, classNumbers):
    classrooms=[]
    roomSize = sorted(roomSize, key=lambda x: x[1], reverse=True)
    for slot in timeSlots:
        classes_in_slot = []
        for c in slot:
            classNum = classNumbers[c]
            classes_in_slot.append([classNum, class_popularity[classNum - 1]])
        classes_in_slot = sorted(classes_in_slot, key=lambda x: x[1], reverse=True)
        # for each time slot, sort classes based on popularity (priority)
        for i in range(0, len(slot)):
            curr_class = classes_in_slot[i]
            curr_room = roomSize[i]
            classrooms.append([curr_class[0], curr_room[0]])
            # assigns classrooms based on popularity (most popular gets largest room)
    classrooms = sorted(classrooms, key=lambda x: x[0])
    return (classrooms)

def studentsForClassHC(classrooms, timeSlots, class_times, s_pref, num_s, num_c, classNumbers, studentNumbers):
    # takes already assigned times and rooms and assigns students
    score = 0
    registration = [[] for i in range(0, num_c)]  # index is class, value is array of students
    for i in range(0, num_s):
        registered_times = []
        for c in s_pref[i]:
            if c in classNumbers:
                classNum = classNumbers[c]
                room = classrooms[classNum - 1][1]
                class_size = (roomSize[room - 1])[1]
                class_time = class_times[classNum - 1]
                if len(registration[classNum - 1]) < class_size and class_time not in registered_times:
                    # if more space in classroom and class fits in student's schedule, register them
                    registration[classNum - 1].append(studentNumbers[i])
                    registered_times.append(class_time)
                    score = score + 1
                    # increments score every time a student is registered for a class
    return registration, score

def scheduleHC(num_c, registration, classrooms, profsClasses, class_times, roomNumbers, file_schedule):
    # takes in all assignments and prints out in new txt file
    orig_stdout = sys.stdout
    sys.stdout = open(file_schedule, "w")
    print("Course\tRoom\tTeacher\tTime\tStudents")
    for i in range(0, num_c):
        students = " ".join(str(item) for item in registration[i])
        if (profsClasses[i][0] == None): #if no professor for a class at the time, blank spot
            prof = ""
        else:
            prof = profsClasses[i][0]
        print("%d\t%s\t%s\t%d\t%s" % (i+1, roomNumbers[int((classrooms[i])[1])-1], prof, int(class_times[i]), students))
    sys.stdout.close()
    sys.stdout = orig_stdout



if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: " + sys.argv[0] + " <student_prefs.txt> <constraints.txt> <schedule.txt>")
        exit(1)

    #Extension test
    start = datetime.now()
    num_t, num_r, num_c, num_s, class_popularity, profsClasses, roomSize, conflict, s_pref, classNumbers, roomNumbers, studentNumbers, levels, subjects, timeslot_overlaps, perfScore = preprocessingHC(sys.argv[1], sys.argv[2])
    timeSlots, class_times = timeForClassHC(conflict, profsClasses, num_t, num_r, num_c,classNumbers, timeslot_overlaps)
    classrooms = roomForClassHC(class_popularity, timeSlots, roomSize, classNumbers)
    registration, score = studentsForClassHC(classrooms, timeSlots, class_times, s_pref, num_s, num_c, classNumbers, studentNumbers)
    scheduleHC(num_c, registration, classrooms, profsClasses, class_times, roomNumbers, sys.argv[3])
    print("Extension Test")
    print("Student Preference Value: ", score)
    print("Best Case Student Value: ", perfScore)
    print("Score Percentage: ", score/perfScore)
    print(datetime.now() - start)
