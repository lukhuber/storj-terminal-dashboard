#!/usr/bin/python3

import re
import os
import sys
import subprocess
import json
import argparse
from datetime import datetime
from enum import Enum

def main():
	# Initialise argument parser
	parser = argparse.ArgumentParser(description="Provides a terminal dashboard for storj nodes")
	parser.add_argument('config_file', nargs='?', default='storj-dashboard.json', help='Path to config file (Default: storj-dashboard.json)')
	
	# Parse arguments
	args = parser.parse_args()
	config_file = args.config_file
	
	try: 
		with open(config_file, 'r') as file:
			config = json.load(file)

		paths = config['nodes']
		earningsCalculator = config['earningscalculator']['path']

		nodes = []

		for name, paths in paths.items():
			nodes.append(Node(name, paths[0], paths[1], earningsCalculator))

		# Display dashboard
		for node in nodes:
			Terminal.print_Node_Details(node)

		Terminal.print_Summary(nodes)

	except FileNotFoundError:
		print(f"Error: The file '{config_file}' was not found. Please check the path and try again.")
	except json.JSONDecodeError:
		print(f"Error: The file '{config_file}' is not a valid JSON file. Please check the content and try again.")
	except Exception as e:
		print(f"An unexpected error occurred: {e}")

# Helper function to add color to terminal output without affecting length
def colored_value(value):
	running  = '\033[31m'
	unknown  = '\033[93m'
	reset    = '\033[0m'

	color = ""

	if value == "running":
		color = running
	elif value == "unknown":
		color = unknown
	else:
		color = '\033[92m'

	return f"{color}{value}{reset}"


def find_second_space_from_right(s):
	# Reverse the input string
	reversed_s = s[::-1]

	# Find all spaces in the string
	space_positions = [pos for pos, char in enumerate(reversed_s) if char == ' ']

	# Check if there are at least 2 spaces
	if len(space_positions) < 2:
		return -1 

	# Position of second space
	second_space_from_right = space_positions[1]

	# Position of second space in original string
	return len(s) - 1 - second_space_from_right


def extract_percentage(s):
	# Search for percentage in string
	match = re.search(r'(\d+\.\d+)%', s)
	if match:
		# Extract percentage as float
		return f'%.2f' % float(match.group(1))
	else:
		return None

# Helper function to calculate the length of a string without ANSI escape sequences
def visible_length(s):
	return len(re.sub(r'\033\[[0-9;]*m', '', s))

# Function to pad a string with spaces considering ANSI escape sequences
def pad_with_color(s, total_length):
	clean_length = visible_length(s)
	padding = total_length - clean_length
	return ' ' * padding + s

class Terminal:
	def print_Node_Details(node):
		name = str(node.name)
		current_total = str(node.current_total)
		estimated_total = str(node.estimated_total)
		disk_used = str(node.disk_used)
		unpaid_data = str(node.unpaid_data)
		deviation_warning = ""

		# Check if deviation_percentage is set and format the warning string with ANSI color codes
		if str(node.deviation_percentage):
			deviation_warning = f"\033[31m Report Deviation: {str(node.deviation_percentage)} % \033[0m"

		# Retrieve and color format values for different satellites
		gcf_sl  = colored_value(node.gcf[Satellite.SL])
		gcf_ap1 = colored_value(node.gcf[Satellite.AP1])
		gcf_eu1 = colored_value(node.gcf[Satellite.EU1])
		gcf_us1 = colored_value(node.gcf[Satellite.US1])

		tcf_sl  = colored_value(node.tcf[Satellite.SL])
		tcf_ap1 = colored_value(node.tcf[Satellite.AP1])
		tcf_eu1 = colored_value(node.tcf[Satellite.EU1])
		tcf_us1 = colored_value(node.tcf[Satellite.US1])

		usf_sl  = colored_value(node.usf[Satellite.SL])
		usf_ap1 = colored_value(node.usf[Satellite.AP1])
		usf_eu1 = colored_value(node.usf[Satellite.EU1])
		usf_us1 = colored_value(node.usf[Satellite.US1])

		print("")
		print("")
		print("═══ {} - Detailed information".format(name))
		print("")
		print("┌───── NODE MAIN STATS ──────┐┌─────────────── FILEWALKER ────────────────┐")
		print("│                            ││                                           │")
		print("│ Current Total: {:>9} $ ││       GARBAGE     TRASH       USED SPACE  │".format(current_total))
		print("│ Estimated Total: {:>7} $ ││       COLLECTOR   CLEANUP     FILEWALKER  │".format(estimated_total))
		print("│                            ││                                           │")
		print("│ Disk Used: {:>15} ││   SL  {:21}{:21}{:20} │".format(disk_used, gcf_sl, tcf_sl, usf_sl))
		print("│ Unpaid Data: {:>13} ││  AP1  {:21}{:21}{:20} │".format(unpaid_data, gcf_ap1, tcf_ap1, usf_ap1))
		print("│                            ││  EU1  {:21}{:21}{:20} │".format(gcf_eu1, tcf_eu1, usf_eu1))
		print("│{:>28}││  US1  {:21}{:21}{:20} │".format(pad_with_color(deviation_warning, 28), gcf_us1, tcf_us1, usf_us1))
		print("│                            ││                                           │  ")
		print("└────────────────────────────┘└───────────────────────────────────────────┘  ")

	def print_Summary(nodes):
		summed_estimated_total = 0

		gcf = {
			Satellite.SL  : 0,
			Satellite.AP1 : 0,
			Satellite.US1 : 0,
			Satellite.EU1 : 0
			}

		tcf = {
			Satellite.SL  : 0,
			Satellite.AP1 : 0,
			Satellite.US1 : 0,
			Satellite.EU1 : 0
			}

		usf = {
			Satellite.SL  : 0,
			Satellite.AP1 : 0,
			Satellite.US1 : 0,
			Satellite.EU1 : 0
			}

		for node in nodes:
			summed_estimated_total += float(node.estimated_total)

			for sat in node.gcf:
				if node.gcf[sat] == "running":
					gcf[sat] += 1

			for sat in node.tcf:
				if node.tcf[sat] == "running":
					tcf[sat] += 1

			for sat in node.usf:
				if node.usf[sat] == "running":
					usf[sat] += 1

		for sat, value in gcf.items():
			gcf[sat] = str(value) + " running"

		for sat, value in tcf.items():
			tcf[sat] = str(value) + " running"

		for sat, value in usf.items():
			usf[sat] = str(value) + " running"
		
		print("")
		print("")
		print("═══════════════════════════ All Nodes - Summary ══════════════════════════")
		print("")
		print("┌───── NODE MAIN STATS ─────┐┌─────────────── FILEWALKER ────────────────┐")
		print("│                           ││                                           │")
		print("│ Estimated total: $ {:6.2f} ││       GARBAGE     TRASH       USED SPACE  │".format(summed_estimated_total))
		print("│                           ││       COLLECTOR   CLEANUP     FILEWALKER  │")
		print("└───────────────────────────┘│                                           │")
		print("                             │   SL  {:12}{:12}{:11} │".format(gcf[Satellite.SL], tcf[Satellite.SL], usf[Satellite.SL]))
		print("                             │  AP1  {:12}{:12}{:11} │".format(gcf[Satellite.AP1], tcf[Satellite.AP1], usf[Satellite.AP1]))
		print("                             │  EU1  {:12}{:12}{:11} │".format(gcf[Satellite.EU1], tcf[Satellite.EU1], usf[Satellite.EU1]))
		print("                             │  US1  {:12}{:12}{:11} │".format(gcf[Satellite.US1], tcf[Satellite.US1], usf[Satellite.US1]))
		print("                             │                                           │  ")
		print("                             └───────────────────────────────────────────┘  ")


class Node:
	def __init__(self, name, logPath, dbPath, earningsCalculator):
		self.name = name
		self.log = ""
		self.earnings = ""
		self.current_total = ""
		self.estimated_total = ""
		self.disk_used = ""
		self.unpaid_data =""
		self.deviation_percentage = ""
		
		# Used to store if USF is running
		self.usf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}

		# Used to store if GCF is running
		self.gcf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}

		# Used to store if TCF is running
		self.tcf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}

		# Parse the log during initiation of this object.
		self.read_Log(logPath)
		self.readEarningsCalculator(dbPath, earningsCalculator)
		self.parse_Earnings_Calculator()


	def read_Log(self, logPath):
		try:
			# Get file size in MB
			total_size_bytes = os.path.getsize(logPath)
			total_size_mb = total_size_bytes / (1024 * 1024)  # Bytes to MB
			total_size_mb_rounded = round(total_size_mb, 1)   # Round to one decimal place

			# Prepare progress bar
			bytes_read = 0
			sys.stdout.write(f'\r[ ~~ ] Reading log of {self.name} ... {bytes_read / (1024 * 1024):.1f}/{total_size_mb_rounded} MB')
			sys.stdout.flush()

			with open(logPath, 'r') as f:
				for line in f:
					bytes_read += len(line.encode('utf-8'))  # Anzahl der gelesenen Bytes aktualisieren


					if "trash-cleanup-filewalker" in line:
						self.parse_TCF_line(line)
					elif "gc-filewalker" in line:
						self.parse_GCF_line(line)
					elif "used-space-filewalker" in line:
						self.parse_USF_line(line)
					elif "Configuration loaded" in line:
						self.reset_all_states()

					sys.stdout.write(f'\r[ ~~ ] Reading log of {self.name} ... {bytes_read / (1024 * 1024):.1f}/{total_size_mb_rounded} MB')
					sys.stdout.flush()

			sys.stdout.write(f'\r[ OK ] Reading log of {self.name} ... {bytes_read / (1024 * 1024):.1f} MB read                          \n')
			sys.stdout.flush()
		except:
			raise


	def reset_all_states(self):
		self.usf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}

		# Used to store if GCF is running
		self.gcf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}

		# Used to store if TCF is running
		self.tcf = {
			Satellite.SL  : "unknown",
			Satellite.AP1 : "unknown",
			Satellite.US1 : "unknown",
			Satellite.EU1 : "unknown"
		}


	def readEarningsCalculator(self, dbPath, earningsCalculator):
		try:
			sys.stdout.write('\r[ ~~ ] Running earnings calculator for ' +  self.name + '\r')
			sys.stdout.flush()
			self.earnings = subprocess.run([sys.executable, earningsCalculator, dbPath], capture_output=True, text=True)
			sys.stdout.write('\r[ OK ] Running earnings calculator for ' +  self.name + '\n')
			sys.stdout.flush()
		except:
			sys.exit("ERROR: Could not run earnings calculator")


	def parse_Earnings_Calculator(self):
		for line in self.earnings.stdout.splitlines():
			if "Total\t\t\t\t\t" in line:
				i = line.rfind(' ')
				self.current_total = line[i+1:]
			if "Estimated total" in line:
				i = line.rfind(' ')
				self.estimated_total = line[i+1:]
			if "Disk Current Total" in line:
				i = find_second_space_from_right(line)
				self.disk_used = line[i+1:]
			if "Total Unpaid Data <─" in line:
				i = find_second_space_from_right(line)
				self.unpaid_data = line[i+1:]
			if "Disk Last Report deviates" in line:
				self.deviation_percentage = extract_percentage(line)


	def parse_TCF_line(self, line):
		for sat in Satellite:
			if "finished successfully" in line and sat.value in line:
				self.tcf[sat] = self.parse_date_and_time(line)
				return
			elif "subprocess started" in line and sat.value in line:
				self.tcf[sat] = "running"
				return


	def parse_GCF_line(self, line):
		for sat in Satellite:
			if "finished successfully" in line and sat.value in line:
				self.gcf[sat] = self.parse_date_and_time(line)
				return
			elif "subprocess started" in line and sat.value in line:
				self.gcf[sat] = "running"
				return		


	def parse_USF_line(self, line):
		for sat in Satellite:
			if "finished successfully" in line and sat.value in line:
				self.usf[sat] = self.parse_date_and_time(line)
				return
			elif "subprocess started" in line and sat.value in line:
				self.usf[sat] = "running"
				return		


	def parse_date_and_time(self, line):
		time = datetime.strptime(line[0:19], '%Y-%m-%dT%H:%M:%S')
		current_time = datetime.now()

		time_difference = current_time - time

		days = time_difference.days
		seconds = time_difference.seconds
		hours, remainder = divmod(seconds, 3600)
		minutes, seconds = divmod(remainder, 60)

		return f'{days}d {hours}h ago'
		

class Satellite(Enum):
	SL  = "1wFTAgs9DP5RSnCqKV1eLf6N9wtk4EAtmN5DpSxcs8EjT69tGE"
	AP1 = "121RTSDpyNZVcEU84Ticf2L1ntiuUimbWgfATz21tuvgk3vzoA6"
	US1 = "12EayRS2V1kEsWESU9QMRseFhdxYxKicsiFmxrsLZHeLUtdps3S"
	EU1 = "12L9ZFwhzVpuEKMUNUqkaTLGzwY9G24tbiigLiXpmZWKwmcNDDs"


if __name__ == "__main__":
	main()