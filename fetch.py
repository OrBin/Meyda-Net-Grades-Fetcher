# -*- coding: utf-8 -*-

from ghost.ghost import Ghost
from bs4 import BeautifulSoup
import sys
import logging
from ghost import TimeoutError


def fetch_grades(year, semester, base_meyda_net_url, id_number, meyda_net_password, timeout=None):

	logging.info("Starting fetching process")
	reload(sys)
	sys.setdefaultencoding("utf-8")

	ghost = Ghost().start()

	page, extra_resources = ghost.open(base_meyda_net_url + "/fireflyweb.aspx", timeout=timeout)

	if not page:
		return None

	result, resources = ghost.set_field_value("input[name=R1C1]", id_number)
	result, resources = ghost.set_field_value("input[name=R1C2]", meyda_net_password)
	page, resources = ghost.call("form", "submit", expect_loading=True)

	page, extra_resources = ghost.open(base_meyda_net_url + "/fireflyweb.aspx?PRGname=MenuCall&ARGUMENTS=-N,-N,-N0013,", timeout=timeout)

	uniq = str(ghost.evaluate('document.getElementsByName("UNIQ")[0].value')[0])

	# R1C2=0 means "שנתי"
	page, extra_resources = ghost.open((base_meyda_net_url +
										"/fireflyweb.aspx?PRGname=Bitsua_maarechet_shaot" +
										"&ARGUMENTS=TZ,UNIQ,MisparSheilta,R1C1,R1C2&TZ=" +
										id_number + "&UNIQ=%s&MisparSheilta=13&R1C1=" + year + "&R1C2=" + semester) % uniq,
										timeout=timeout)

	logging.info("Starting parsing process")
	parser = BeautifulSoup(str(page.content), "lxml")
	table = parser.find("table", class_="SortMe")
	table_thead = table.find("thead")

	HEADERS = ["סמסטר", "שם קורס", "מועד", "ציון", "סוג מקצוע"]
	table_col_dict = {}

	index = 0
	for th in table_thead.find("tr").find_all("th"):
		current_header = th.text.strip().encode("utf-8")
		if current_header in HEADERS:
			table_col_dict[current_header] = index
		index += 1

	curr_grades = {}

	def extract_text_by_key(key):
		return line_cells[table_col_dict[key]].text.strip().encode("utf-8")

	for tr in table.find("tbody").find_all("tr"):
		line_cells = tr.find_all("td")
		if "שעור" in extract_text_by_key("סוג מקצוע"):
			ukey =  extract_text_by_key("שם קורס") + ";" +  extract_text_by_key("סמסטר") + ";" + extract_text_by_key("מועד")
			curr_grades[ukey] = extract_text_by_key("ציון")

	return curr_grades


def try_fetching(year, semester, base_meyda_net_url, id_number, meyda_net_password, number_of_retries, timeout=None):

	# Fetching current grades
	for i in range(1, number_of_retries+1):
		try:
			logging.info("Trying to fetch grades, attempt %s of %s" % (i, number_of_retries))
			results = fetch_grades(year, semester, base_meyda_net_url, id_number, meyda_net_password, timeout=timeout)
			if results:
				return results
		except TimeoutError:
			if i != number_of_retries:
				logging.info("Timeout reached. Retrying...")
			else:
				logging.info("Maximum attempts reached. Exiting.")
				return None