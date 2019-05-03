#!/usr/bin/python3.7

import argparse
import asyncio
import logging
import os
import sys

from sis import classes, enrollments, terms
from ucbhr import info as ucbhr_info
 
def parse_course(course):
	'''Parse {year}-{semester}-{class_number}.'''
	year, semester, class_number = course.split('-', 3)
	# type check
	year = int(year) ; class_number = int(class_number)
	# validate semester
	semesters = ['summer', 'spring', 'fall']
	semester = semester.lower()
	assert semester in semesters, f"{semester} not one of {semesters}"
	return year, semester, class_number

async def instructor_emails(term_id, class_number):
	'''Return the business emails of instructors for courses matching
	   {term_id} and {class_number.'''
	# get the instructors of our course. sis only has their uids, not emails.
	uids = await classes.get_instructors(
		SIS_CLASSES_ID, SIS_CLASSES_KEY,
		term_id, class_number, False, 'campus-uid'
	)

	# ask hr for the emails
	emails = []
	for uid in uids:
		# get all emails
		items = await ucbhr_info.get(UCB_HR_ID, UCB_HR_KEY, uid, 'campus-uid')
		# extract the business (berkeley.edu) addresses
		emails += ucbhr_info.emails(items, 'BUSN')
	return emails

async def student_emails(term_id, class_number):
	'''Return the campus emails of students in courses matching
	   {term_id} and {class_number.'''
	# get the section data for the specified course
	section = await classes.get_section_by_id(
		SIS_CLASSES_ID, SIS_CLASSES_KEY, term_id, class_number
	)

	# isolate the subject area and catalog number, e.g. STAT C8
	subject_area   = enrollments.section_subject_area(section)
	catalog_number = enrollments.section_catalog_number(section)

	# get enrollments in matching sections for the term id, subject, and number
	student_enrollments = await enrollments.get_enrollments(
		SIS_ENROLLMENTS_ID, SIS_ENROLLMENTS_KEY,
		term_id, subject_area, catalog_number
	)

	# extract the student email addresses
	return enrollments.get_enrollment_emails(student_enrollments)

async def main():
	logging.basicConfig(stream=sys.stdout)
	logger = logging.getLogger()
	logger.setLevel(logging.ERROR)

	# check for creds in environment and set them as global vars
	required_env_vars = [
			'SIS_CLASSES_ID', 'SIS_CLASSES_KEY',
		'SIS_ENROLLMENTS_ID', 'SIS_ENROLLMENTS_KEY',
			  'SIS_TERMS_ID', 'SIS_TERMS_KEY',
				 'UCB_HR_ID', 'UCB_HR_KEY',
	]
	for v in required_env_vars:
		assert v in os.environ, f"{v} not defined in environment."
		globals()[v] = os.environ[v]

	# arg parsing
	parser = argparse.ArgumentParser(
        description="Get UCB course enrollee and instructor email addresses.")
	parser.add_argument('-d', dest='debug', action='store_true',
		help='set debug log level')
	parser.add_argument('course', metavar='year-semester-classnum',
		help='e.g. "2019-summer-12345"')
	parser.add_argument('constituents', choices=['students', 'instructors'],
		help='constituents')
	args = parser.parse_args()
	
	if args.debug: logger.setLevel(logging.DEBUG)

	logger.debug(f"course: {args.course}")
	logger.debug(f"constituents: {args.constituents}")

	year, semester, class_number = parse_course(args.course)

	# fetch the SIS term id, e.g. 2195
	term_id = await terms.get_term_id_from_year_sem(
		SIS_TERMS_ID, SIS_TERMS_KEY, year, semester
	)
	term_id = int(term_id)
	logger.debug(f"{term_id} {class_number}")

	if args.constituents == 'students':
		emails = await student_emails(term_id, class_number)
	elif args.constituents == 'instructors':
		emails = await instructor_emails(term_id, class_number)

	for email in emails: print(email)

# main
asyncio.run(main())
