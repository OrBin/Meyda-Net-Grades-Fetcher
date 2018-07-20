# -*- coding: utf-8 -*-

import sys
import fetch
import logging
import requests
from datetime import datetime
import os
import files

reload(sys)
sys.setdefaultencoding("utf-8")

DATA_FILE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/" + "last_grades.json"
CONF_FILE_PATH = os.path.abspath(os.path.dirname(__file__)) + "/" + "config.json"
FETCH_TRIES = 5


logging.basicConfig(filename=os.path.abspath(os.path.dirname(__file__)) + "/" + 'log.txt',
					filemode='a',
					level=logging.DEBUG,
					format="%(asctime)s %(levelname)s %(module)s %(message)s",
					datefmt='%Y-%m-%d %H:%M:%S %Z')
logging.info("**************** Starting job ****************")

config = files.read_configuration_file(CONF_FILE_PATH)
previous_grades = files.read_saved_grades(DATA_FILE_PATH)
grades_to_save = {"users": {}}

for user in config["users"]:

	results = fetch.try_fetching("2017", "0", user["base_meyda_net_url"], user["id_number"], user["meyda_net_password"], FETCH_TRIES, timeout=None)

	if not results:
		if previous_grades and (str(user["id_number"]) in previous_grades["users"]):
			grades_to_save["users"][str(user["id_number"])] = previous_grades["users"][str(user["id_number"])]
		continue
	grades_to_save["users"][str(user["id_number"])] = {"grades": results, "time": int((datetime.now() - datetime(1970, 1, 1)).total_seconds())}

	try:
		# If there are no previous grades, there is nothing to compare to
		if previous_grades and (str(user["id_number"]) in previous_grades["users"]):
			user_previous_grades = previous_grades["users"][str(user["id_number"])]

			if user_previous_grades and len(user_previous_grades) > 0:

				# Every difference is a tuple of ("course;semester;moed", prev_grade, curr_grade)
				differences = []

				# Add differences to the list
				for key, curr_grade in results.iteritems():
					ukey = key.decode("utf-8")
					if ukey not in user_previous_grades["grades"].keys():
						differences.append((ukey, None, curr_grade))
					elif curr_grade != user_previous_grades["grades"][ukey]:
							differences.append((ukey, user_previous_grades["grades"][ukey], curr_grade))

				if len(differences) == 0:
					logging.info("---No Changes---")
				else:
					email_text = ""
					for diff in differences:
						diff_fields = map(str, diff[0].split(";")) + [diff[1], diff[2]]
						if not diff_fields[3]:
							diff_fields[3] = "לא קיים"

						logging.info("קורס %s סמסטר %s מועד %s:" % tuple(diff_fields[0:3]))
						logging.info("השתנה מ-%s ל-%s" % tuple(diff_fields[3:5]))

						email_text += "הציון בקורס %s סמסטר %s מועד %s השתנה מ-%s ל-%s\n\n" % tuple(diff_fields)

					email_request_url = config["api_base_url"] + "/messages"
					email_request_data = {"from": "Meyda Net Grades Fetcher <%s>" % config["sending_email_address"],
											"to": user["email_address"],
											"subject": "ציון חדש במידע-נט",
											"text": email_text}
					email_response = requests.post(email_request_url, auth=("api", config["api_key"]), data=email_request_data)

	except Exception as exc:
		logging.exception(exc)

files.save_grades(grades_to_save, DATA_FILE_PATH)