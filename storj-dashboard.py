#!/usr/bin/python3

import re
import os
import sys
import time
import subprocess
import json
from datetime import datetime
from enum import Enum

def main():
	try: 
		with open('storj-dashboard.json', 'r') as file:
			config = json.load(file)

		paths = config['nodes']
		earningsCalculator = config['earningscalculator']['path']

		nodes = []

		for name, paths in paths.items():
			nodes.append(Node(name, paths[0], paths[1], earningsCalculator))

		# Show dashboard
		for node in nodes:
			Terminal.print_Node_Details(node)

		Terminal.print_Summary(nodes)

	except Exception as e:
		raise

# Helper function to add color without affecting length
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
    # String umkehren
    reversed_s = s[::-1]

    # Positionen der Leerzeichen im umgekehrten String finden
    space_positions = [pos for pos, char in enumerate(reversed_s) if char == ' ']

    # Prüfen, ob es mindestens zwei Leerzeichen gibt
    if len(space_positions) < 2:
        return -1  # Oder eine andere angemessene Rückgabe, wenn es weniger als zwei Leerzeichen gibt

    # Position des zweiten Leerzeichens vom Ende
    second_space_from_right = space_positions[1]

    # Position im ursprünglichen String
    return len(s) - 1 - second_space_from_right


def extract_percentage(s):
    # Suche nach einem Muster, das einer Zahl mit einem Dezimalpunkt und einem %-Zeichen entspricht
    match = re.search(r'(\d+\.\d+)%', s)
    if match:
        # Extrahiere den gefundenen Prozentwert als Float
        return f'%.2f' % float(match.group(1))
    else:
        return None

class Terminal:
	def print_Node_Details(node):
		name = str(node.name)
		current_total = str(node.current_total)
		estimated_total = str(node.estimated_total)
		disk_used = str(node.disk_used)
		unpaid_data = str(node.unpaid_data)
		deviation_warning = ""

		if str(node.deviation_percentage):
			deviation_warning = f"\033[31m Report Deviation: {str(node.deviation_percentage)} % \033[0m"

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
		print("┌───── NODE MAIN STATS ─────┐┌─────────────── FILEWALKER ────────────────┐")
		print("│                           ││                                           │")
		print("│ Current Total: {:>8} $ ││       GARBAGE     TRASH       USED SPACE  │".format(current_total))
		print("│ Estimated Total: {:>6} $ ││       COLLECTOR   CLEANUP     FILEWALKER  │".format(estimated_total))
		print("│                           ││                                           │")
		print("│ Disk Used: {:>14} ││   SL  {:21}{:21}{:20} │".format(disk_used, gcf_sl, tcf_sl, usf_sl))
		print("│ Unpaid Data: {:>12} ││  AP1  {:21}{:21}{:20} │".format(unpaid_data, gcf_ap1, tcf_ap1, usf_ap1))
		print("│                           ││  EU1  {:21}{:21}{:20} │".format(gcf_eu1, tcf_eu1, usf_eu1))
		print("│{:>27}││  US1  {:21}{:21}{:20} │".format(deviation_warning, gcf_us1, tcf_us1, usf_us1))
		print("│                           ││                                           │  ")
		print("└───────────────────────────┘└───────────────────────────────────────────┘  ")

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
			# Dateigröße in Megabyte ermitteln
			total_size_bytes = os.path.getsize(logPath)
			total_size_mb = total_size_bytes / (1024 * 1024)  # Bytes in Megabyte umrechnen
			total_size_mb_rounded = round(total_size_mb, 1)   # Auf eine Stelle nach dem Dezimalpunkt runden

			# Fortschrittsanzeige vorbereiten
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
			self.earnings = subprocess.run(['python3', earningsCalculator, dbPath], capture_output=True, text=True)
			sys.stdout.write('\r[ OK ] Running earnings calculator for ' +  self.name + '\n')
			sys.stdout.flush()
		except:
			sys.exit("ERROR: Could not run earnings calculator")


	def parse_Earnings_Calculator(self):
		#print(self.earnings.stdout)
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