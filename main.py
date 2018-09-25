#possible api to use in the future: https://github.com/ucfopen/canvasapi

import json

from student_identities import *

import requests

def getid(name, ids, names):
	for i in range(len(names)):
		if names[i] == name:
			return ids[i]
	return "could not find"

def getname(idnum, ids, names):
	for i in range(len(ids)):
		if ids[i] == idnum:
			return names[i]
	return "could not find"

def readgradesfile(filename, ids, names):
	'''
	returns array of json data of students
	'''
	json_data_array = []
	text_file = open(filename, "r")
	submissions = text_file.read().split('--------------------------------------------------------------------------------')
	del submissions[0]
	#print(submissions[0])
	for i in range(len(submissions)):
		#print(i)
		submission_json_data = {}
		lines = submissions[i].split('\n')
		del lines[0]
		#print(lines[0])
		comment_string = ""
		for j in range(len(lines)):
			if lines[j] == "":
				break
			elif j <= 5:
				entries_without_strip = lines[j].split('|')
				entries_in_lines = []
				for elem in entries_without_strip:
				    entries_in_lines.append(elem.replace(' ',''))
				#print(entries_in_lines[0])
				if j == 0:
					#first line data
					submission_json_data['timegrading'] = entries_in_lines[0].replace('Timeofgrading','')
					submission_json_data['grade'] = entries_in_lines[1]
					submission_json_data['studentid'] = entries_in_lines[2]
					submission_json_data['studentname'] = getname(entries_in_lines[2], ids, names)
				else:
					field = entries_in_lines[0]
					data = entries_in_lines[1].replace('points','')
					submission_json_data[field] = data
			else :
				try:
					nextline = lines[j + 2]
					comment_string = comment_string + lines[j] + '\n'
				except IndexError:
					#end of new line data
					comment_string = comment_string + lines[j]
					submission_json_data['comment'] = comment_string
		if submission_json_data != {}:
			json_data = json.dumps(submission_json_data)
			json_data_array.append(json_data)
		#break
	#print(json_data_array)
	return json_data_array

def getgradecomment(name, submissions):
	for submission in submissions:
		submissionjson = json.loads(submission)
		if submissionjson['studentname'] == name:
			return submissionjson['grade'], submissionjson['comment'].replace('\\n','\n').replace('\\t','\t')
	return 'n/a', 'could not find data'

def uploadgrade(token, courseurl, studentid, assignmentid, submissiondata):
	url = courseurl + "/assignments/" + assignmentid + "/submissions/update_grades/"
	print(url)
	json_data = json.loads(submissiondata)
	postdata = {
		"grade_data": {
			studentid: {
				"text_comment": json_data["comment"],
				"posted_grade": json_data["grade"]
			}
		}
	}
	print(postdata)
	json_data = json.dumps(postdata)
	tokenstring = "Bearer " + token
	headers = {"content-type": "application/json", "Accept-Charset": "UTF-8", "Authorization": tokenstring}
	r = requests.post(url, data = json_data, headers = headers)
	print(r)

def getcanvasstudentid(token, courseurl, name):
	url = courseurl + "/search_users"
	print(url)
	getdata = {
		"search_term": name
	}
	print(getdata)
	json_data = json.dumps(getdata)
	tokenstring = "Bearer " + token
	headers = {"content-type": "application/json", "Accept-Charset": "UTF-8", "Authorization": tokenstring}
	r = requests.get(url, data = json_data, headers = headers).json()
	print(r)
	#print(r.text)

def parseLinkHeader(lh):
	'''Parse the Link HTTP header to see how the server has paginated users.
	  It is of the form: "<URL>; rel="context",<URL>; rel="context",..."
	  Return a dictionary of 'current', 'next', 'last', 'first' (and 'prev')
	  links.'''
	links = map(lambda x: x.split('; rel='), lh.split(','))
	lc = {}
	for link in links:
		url = link[0][1:-1] # trim '<' and '>'
		cxt = link[1][1:-1] # trim '"'
		lc[cxt] = url
	return lc

def getallstudentdata(token, courseurl):
	url = courseurl + "/users"
	print(url)
	getdata = {
		"enrollment_type": "student"
	}
	print(getdata)
	json_data = json.dumps(getdata)
	tokenstring = "Bearer " + token
	headers = {"content-type": "application/json", "Accept-Charset": "UTF-8", "Authorization": tokenstring}
	def getstudentshelper(current_url):
		r = requests.get(current_url, data = json_data, headers = headers)
		print(r)
		data = r.json()
		try:
			links = parseLinkHeader(r.headers['link'])
		except KeyError:
			return data

		# We are not at the last page
		if links['current'] != links['last']:
			data += getstudentshelper(links['next'])
		return data
	allstudents = getstudentshelper(url)
	allstudentsidname = []
	for student in allstudents:
		newstudentdata = {}
		newstudentdata['id'] = student['id']
		name = student['name']
		firstlast = name.split(' ')
		lastfirst = firstlast[-1] + firstlast[0]
		newstudentdata['name'] = lastfirst.lower().replace('\'','')
		allstudentsidname.append(newstudentdata)
	return allstudentsidname

def findid(studentnames, name):
	for student in studentnames:
		if student['name'] == name:
			return student['id']
	return -1

if __name__ == '__main__':
	configfile = open('config/config.json')
	config = json.load(configfile)
	canvastoken = config["CanvasAuthToken"]
	courseurl = config["CourseURL"]
	assignmentid = config["AssignmentId"]
	gradesfile = config["GradesFile"]
	submissions = readgradesfile(gradesfile, ids, nmes)
	nameswithspaces = config["NamesWithSpaces"]
	if nameswithspaces == []:
		nameswithspaces = getallstudentdata(canvastoken, courseurl)
		#PRINT ALL STUDENTS
		#print(nameswithspaces)
		with open('config/config.json', "r+") as f:
			data = json.load(f)
			tmp = data["NamesWithSpaces"]
			data["NamesWithSpaces"] = nameswithspaces

			f.seek(0)  # rewind
			json.dump(data, f)
			f.truncate()
	for sub in submissions:
		json_sub = json.loads(sub)
		#print(json_sub)
		name = json_sub['studentname']
		canvas_student_id = findid(nameswithspaces, name)
		if canvas_student_id != -1:
			#print(canvas_student_id)
			studentgrading = {}
			studentgrading['grade'] = json_sub['grade'].split('/')[0]
			studentgrading['comment'] = json_sub['comment']
			studentgradingjson = json.dumps(studentgrading)
			#print(studentgradingjson)
			#uploadgrade(canvastoken, courseurl, canvas_student_id, assignmentid, studentgradingjson)
			break