import os
import logging
import sys
import json


def read_configuration_file(file_path):
	if not os.path.isfile(file_path):
		logging.critical("Could not find configuration file '%s'", file_path)
		sys.exit(1)
	else:
		logging.info("Reading configuration file")
		with open(file_path, "r") as f:
			return json.loads("".join(f.readlines()))


def read_saved_grades(file_path):
	# Reading previous grades from file
	if not os.path.isfile(file_path):
		logging.info("No previous file")
	else:
		logging.info("Reading previous file")
		with open(file_path, "r") as f:
			return json.loads("".join(f.readlines()))


def save_grades(grades_to_save, file_path):
	try:
		# Writing current grades to file
		data_json = json.dumps(grades_to_save, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
		with open(file_path, "w") as f:
			f.write(data_json)
	except Exception as exc:
		logging.exception(exc)

