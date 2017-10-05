# -*- coding: utf-8 -*-

import sys
import fetch
import logging
import requests
import json
from datetime import datetime
import os
from ghost import TimeoutError

reload(sys)
sys.setdefaultencoding("utf-8")

DATA_FILE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/" + "last_grades.json"
CONF_FILE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/" + "config.json"
FETCH_TRIES = 5

prev_grades = None
prev_timestamp = None
curr_grades = None
config = None

logging.basicConfig(filename=os.path.abspath(os.path.dirname(__file__)) + "/" + 'log.txt',
					filemode='a',
					level=logging.DEBUG,
					format="%(asctime)s %(levelname)s %(module)s %(message)s",
					datefmt='%Y-%m-%d %H:%M:%S %Z')

logging.info("**************** Starting service ****************")
logging.debug("Debug message for testing")

if not os.path.isfile(CONF_FILE_PATH):
	logging.critical("No configuration file found at '%s'", CONF_FILE_PATH)
	sys.exit(1)
else:
	logging.info("Reading configuration file")
	with open(CONF_FILE_PATH, "r") as f:
		config = json.loads("".join(f.readlines()))

for user in config["users"]:
	base_meyda_net_url = user["base_meyda_net_url"]
	id_number = user["id_number"]
	meyda_net_password = user["meyda_net_password"]
	email_address = user["email_address"]

	curr_timestamp = int((datetime.now() - datetime(1970,1,1)).total_seconds())

	# Reading previous grades from file
	if not os.path.isfile(DATA_FILE_PATH):
		logging.info("No previous file")
	else:
		logging.info("Reading previous file")
		with open(DATA_FILE_PATH, "r") as f:
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
		with open(DATA_FILE_PATH, "w") as f:
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
																					   diff[3] if diff[3] else "לא קיים", # prev_grade
																					   diff[4])  # curr_grade

				res = requests.post("{}/messages".format(config["api_base_url"]),
				                    auth=("api", config["api_key"]),
				                    data={"from": "Meyda Net Grades Fetcher <{}>".format(config["sending_email_address"]),
				                          "to": email_address,
				                          "subject": "ציון חדש במידע-נט",
				                          "text": email_text})

	except Exception as exc:
		logging.exception(exc)
