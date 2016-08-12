# -*- coding: utf-8 -*-

import sys
import fetch
import time
import logging
import smtplib
from email.mime.text import MIMEText
import gc

reload(sys)
sys.setdefaultencoding("utf-8")

logging.basicConfig(filename='log.txt',
					filemode='a',
					level=logging.DEBUG,
					format="%(asctime)s %(levelname)s %(module)s %(message)s",
					datefmt='%Y-%m-%d %H:%M:%S %Z')

logging.info("**************** Starting service ****************")
logging.debug("Debug message for testing")
file = open("login_data.txt", "r")
base_meyda_net_url = file.readline().strip()
id_number = file.readline().strip()
meyda_net_password = file.readline().strip()
email_address = file.readline().strip()
email_pass = file.readline().strip()
file.close()

curr_grades = fetch.fetch_grades("2016", "0", base_meyda_net_url, id_number, meyda_net_password)

while True:
	try:
		logging.info("Starting a new iteration. Sleeping first")
		time.sleep(60*15) # Sleep 15 minutes
		logging.info("Woke up")

		prev_grades = curr_grades
		curr_grades = fetch.fetch_grades("2016", "0", base_meyda_net_url, id_number, meyda_net_password)

		# Every difference will be a tuple of (course, semester, moed, prev_grade, curr_grade)
		differences = []

		# Add differences to the list
		for keys, curr_grade in curr_grades.iteritems():
			if keys not in prev_grades.keys():
				differences.append((keys[0], keys[1], keys[2], None, curr_grade))
			else:
				if curr_grade != prev_grades[keys]:
					differences.append((keys[0], keys[1], keys[2], prev_grades[keys], curr_grade))

		if len(differences) == 0:
			logging.info("לא השתנה כלום")
		else:
			email_text = ""

			for diff in differences:
				logging.info("קורס %s סמסטר %s מועד %s:" % (diff[0], diff[1], diff[2]))
				logging.info("השתנה מ-%s ל-%s" % (diff[3] if diff[3] else "לא קיים", diff[4]))

				email_text += "הציון בקורס %s סמסטר %s מועד %s השתנה מ-%s ל-%s\n\n" % (diff[0], # course
																					diff[1], # semester
																					diff[2], # moed
																					diff[3] if diff[3] else "לא קיים", # prev_grade
																					diff[4]) # curr_grade

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
		gc.collect()
	except Exception as exc:
		logging.exception(exc)
