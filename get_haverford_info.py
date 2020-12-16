#!/usr/bin/python

import csv
import sys

def get_data_list_of_dicts(filename):
  list = []
  with open(filename) as f:
    f_csv = csv.DictReader(f)
    for row in f_csv:
      list.append(row)
  return list

def get_room_sizes(list_of_dicts):
  room_sizes_dict = {}
  for dict in list_of_dicts:
    room = dict["Facil ID 1"]
    status = dict["Status"]
    course = dict["Course ID"]
    campus = dict["College"]
    if status == "E" and campus == "H" and not room == "":
      if room in room_sizes_dict:
        if course in room_sizes_dict[room]:
          room_sizes_dict[room][course] = room_sizes_dict[room][course] + 1
        else:
          room_sizes_dict[room][course] = 1
      else:
        room_sizes_dict[room] = {}
        room_sizes_dict[room][course] = 1

  room_capacities = {}
  for room in room_sizes_dict:
    capacity = 0
    for course in room_sizes_dict[room]:
      if room_sizes_dict[room][course] > capacity:
        capacity = room_sizes_dict[room][course]
    room_capacities[room] = capacity
  return room_capacities

def get_student_prefs_enrolled(list_of_dicts):
  student_prefs = {}
  for dict in list_of_dicts:
    student = dict["Student"]
    course = dict["Course ID"]
    status = dict["Status"]
    if status == "E":
      if student in student_prefs:
        student_prefs[student].append(course)
      else:
        student_prefs[student] = [course]
  return student_prefs

def get_courses(list_of_dicts):
  courses = {}
  for dict in list_of_dicts: 
    course = dict["Course ID"]
    campus = dict["College"]
    if not course in courses and campus == "H":
      courses[course] = dict
  return courses

def get_prof_courses(list_of_dicts):
  profs = {}
  for dict in list_of_dicts:
    prof = dict["Instructor ID"]
    course = dict["Course ID"]
    campus = dict["College"]
    if not prof == "" and campus == "H":
      if prof in profs:
        if not course in profs[prof]:
          profs[prof].append(course)
      else:
        profs[prof] = [course]
  return profs 

def get_class_times(list_of_dicts):
  times = []
  for dict in list_of_dicts:
    start = dict["Srt1 AM/PM"]
    end = dict["End 1 AMPM"]
    days = dict["Days 1"]
    class_time = (start, end, days)
    campus = dict["College"]
    if not class_time in times and campus == "H" and not start == "" \
        and not end == "" and not days == "":
      times.append(class_time)
  return times

def get_extras(list_of_dicts):
  levels = []
  subjects = []
  class_times = []
  for dict in list_of_dicts:
    status = dict["Status"]
    level = dict["Level"]
    subject = dict["Subject"]
    start = dict["Srt1 AM/PM"]
    end = dict["End 1 AMPM"]
    days = dict["Days 1"]
    class_time = (start, end, days)
    if status == 'E':
      levels.append(level)
      subjects.append(subject)
      class_times.append(class_time)
  return levels, subjects, class_times

# One possibility for how to find out which labs go with which courses.
# Currently catches some "labs" that aren't actually labs for those courses.
# Course '333' seems especially to be a strange corner case.
# The issue may also be that this doesn't take sections into account in matching.
#def get_lab_courses(list_of_dicts):
#  lab_courses = {}
#  student_courses = get_student_prefs_enrolled(list_of_dicts)
#  courses = get_courses(list_of_dicts)
#  for dict in list_of_dicts:
#    course = dict["Course ID"]
#    dept = dict["Subject"]
#    level = dict["Level"]
#    student = dict["Student"]
#    units = dict["Unit Taken"]
#    campus = dict["College"]
#    if units == "0" and campus == "H":  # we think this is a lab class
#      all_courses = student_courses[student]
#      for enrolled_course in all_courses:
#        if not enrolled_course == course and enrolled_course in courses:
#          course_dict = courses[enrolled_course]
#          enrolled_dept = course_dict["Subject"]
#          enrolled_level = course_dict["Level"]
#          enrolled_units = course_dict["Unit Taken"]
#          enrolled_campus = course_dict["College"]
#          if enrolled_units > 0 and enrolled_dept == dept and enrolled_level == level \
#              and enrolled_campus == campus:
#            print enrolled_course + " " + course
#            if enrolled_course in lab_courses:
#              if not course in lab_courses[enrolled_course]:
#                lab_courses[enrolled_course].append(course)
#            else:
#              lab_courses[enrolled_course] = [course]
#  return lab_courses

def write_prefs_to_file(list_of_dicts, filename):
  student_prefs = get_student_prefs_enrolled(list_of_dicts)
  f = open(filename, 'w')
  f.write("Students\t" + str(len(student_prefs)) + "\n")
  for student in student_prefs:
    towrite = student + "\t"
    for course in student_prefs[student]:
      towrite = towrite + course + " "
    towrite = towrite + "\n"
    f.write(towrite)

def write_class_times_to_file(list_of_dicts, f):
  class_times = get_class_times(list_of_dicts)
  f.write("Class Times\t" + str(len(class_times)) + "\n")
  i = 1
  for (start, end, days) in class_times:
    f.write(str(i) + "\t" + start + "\t" + end + "\t" + days + "\t\n")
    i = i + 1

def write_rooms_to_file(list_of_dicts, f):
  room_capacities = get_room_sizes(list_of_dicts)
  f.write("Rooms\t" + str(len(room_capacities)) + "\n")
  for room in room_capacities:
    f.write(room + "\t" + str(room_capacities[room]) + "\n")

def write_num_classes_to_file(list_of_dicts, f):
  num_classes = len(get_courses(list_of_dicts))
  f.write("Classes\t" + str(num_classes) + "\n")

def write_teachers_to_file(list_of_dicts, f):
  prof_courses = get_prof_courses(list_of_dicts)
  num_profs = len(prof_courses)
  courses = get_courses(list_of_dicts)
  f.write("Teachers\t" + str(num_profs) + "\n")
  for course in courses:
    f.write(course + "\t")
    f.write(courses[course]["Instructor ID"])
    f.write("\n")

def write_extras_to_file(list_of_dicts, f):
  levels, subjects, class_times = get_extras(list_of_dicts)
  f.write("Level\tSubject\tStart\tEnd\tDays\n")
  for i in range(0, len(levels)):
    f.write(str(levels[i]) + "\t" + subjects[i] + "\t" + class_times[i][0] + "\t" + class_times[i][1] + "\t" + class_times[i][2] + "\t\n")



def write_constraints_to_file(list_of_dicts, filename):
  f = open(filename, 'w')
  write_class_times_to_file(list_of_dicts, f)
  write_rooms_to_file(list_of_dicts, f)
  write_num_classes_to_file(list_of_dicts, f)
  write_teachers_to_file(list_of_dicts, f)
  write_extras_to_file(list_of_dicts, f)
  f.close()

if len(sys.argv) != 4:
  print("Usage: " + sys.argv[0] + " <enrollment.csv> <student_prefs.txt> <constraints.txt>")
  exit(1) 
list_of_dicts = get_data_list_of_dicts(sys.argv[1])
write_prefs_to_file(list_of_dicts, sys.argv[2])
write_constraints_to_file(list_of_dicts, sys.argv[3])
