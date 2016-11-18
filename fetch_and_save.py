# -*- coding: utf-8 -*-

import sys
import fetch
import logging
import smtplib
from email.mime.text import MIMEText
import json
from datetime import datetime
import os
from ghost import TimeoutError

reload(sys)
sys.setdefaultencoding("utf-8")

FILENAME = "last_grades.json"
FULL_FILE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/" + FILENAME
FETCH_TRIES = 5

logging.basicConfig(filename=os.path.abspath(os.path.dirname(__file__)) + "/" + 'log.txt',
					filemode='a',
					level=logging.DEBUG,
					format="%(asctime)s %(levelname)s %(module)s %(message)s",
					datefmt='%Y-%m-%d %H:%M:%S %Z')

logging.info("**************** Starting service ****************")
logging.debug("Debug message for testing")
file = open(os.path.abspath(os.path.dirname(__file__)) + "/" + "login_data.txt", "r")
base_meyda_net_url = file.readline().strip()
id_number = file.readline().strip()
meyda_net_password = file.readline().strip()
email_address = file.readline().strip()
email_pass = file.readline().strip()
file.close()

prev_grades = None
prev_timestamp = None
curr_grades = None
curr_timestamp = int((datetime.now() - datetime(1970,1,1)).total_seconds())

# Reading previous grades from file
if not os.path.isfile(FULL_FILE_PATH):
	logging.info("No previous file")
else:
	logging.info("Reading previous file")
	with open(FULL_FILE_PATH, "r") as f:
		prev_data_from_file = json.loads("".join(f.readlines()))
		prev_timestamp = prev_data_from_file[u'time']
		prev_grades = prev_data_from_file[u'grades']

# Fetching current grades
for i in range(1, FETCH_TRIES+1):
	try:
		logging.info("Trying to fetch grades, attempt %s of %s" % (i, FETCH_TRIES))
		curr_grades = fetch.fetch_grades("2017", "0", base_meyda_net_url, id_number, meyda_net_password, timeout=None)
		break
	except TimeoutError as timeout_err:
		if i != FETCH_TRIES:
			logging.info("Timeout reached. Retrying...")
		else:
			logging.info("Maximum attempts reached. Exiting.")
			sys.exit(1)

try:
	# Writing current grades to file
	data = {"time": curr_timestamp, "grades": curr_grades}
	data_json = json.dumps(data, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
	with open(FULL_FILE_PATH, "w") as f:
		f.write(data_json)

	# If there are no previous grades, there is nothing to compare to
	if not prev_grades:
		sys.exit(0)

	# Every difference will be a tuple of ("course;semester;moed", prev_grade, curr_grade)
	differences = []

	# Add differences to the list
	for key, curr_grade in curr_grades.iteritems():
		ukey = key.decode("utf-8")
		if ukey not in prev_grades.keys():
			differences.append((ukey, None, curr_grade))
		else:
			if curr_grade != prev_grades[ukey]:
				differences.append((ukey, prev_grades[ukey], curr_grade))

	if len(differences) == 0:
		logging.info("---No Changes---")
	else:
		email_text = ""

		for diff in differences:
			course, semester, moed = map(str, diff[0].split(";"))
			diff = (course, semester, moed, str(diff[1]), diff[2])

			logging.info("קורס %s סמסטר %s מועד %s:" % (diff[0], diff[1], diff[2]))
			logging.info("השתנה מ-%s ל-%s" % (diff[3] if diff[3] else "לא קיים", diff[4]))

			email_text += "הציון בקורס %s סמסטר %s מועד %s השתנה מ-%s ל-%s\n\n" % (diff[0],  # course
																				   diff[1],  # semester
																				   diff[2],  # moed
																				   diff[3] if diff[
																					   3] else "לא קיים",
																				   # prev_grade
																				   diff[4])  # curr_grade

			msg = MIMEText(email_text)

			msg['Subject'] = 'ציון חדש במידע-נט'
			msg['From'] = email_address
			msg['To'] = email_address

			s = smtplib.SMTP('smtp.gmail.com', 587)
			s.ehlo()
			s.starttls()
			s.login(email_address, email_pass)
			s.sendmail(email_address, [email_address], msg.as_string())
			s.quit()

except Exception as exc:
	logging.exception(exc)
