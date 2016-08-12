# -*- coding: utf-8 -*-

import sys
import fetch
import time
import logging
import smtplib
from email.mime.text import MIMEText
import gc
import json 
from datetime import datetime

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

curr_grades = None

#try:
curr_grades = fetch.fetch_grades("2016", "0", base_meyda_net_url, id_number, meyda_net_password)
data = {"time": int((datetime.now() - datetime(1970,1,1)).total_seconds()),
	"grades": curr_grades}
print data
data_json = json.dumps(data, ensure_ascii=False)
print
print
print
print
print
print data_json
with open("last_grades.json", "w") as f:
	f.write(data_json)
#except Exception as exc:
#	print exc
#	logging.exception(exc)
