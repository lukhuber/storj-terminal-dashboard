#!/usr/bin/python3

import re
import os
import sys
import subprocess
import json
import glob
import argparse
from enum import Enum
from datetime import datetime, timezone
from colorama import init, Fore, Style


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
    running = Fore.RED
    unknown = Fore.YELLOW
    offline = Fore.RED
    default = Fore.GREEN

    color = default

    if value == "running":
        color = running
    elif value == "unknown":
        color = unknown
    elif value == "offline":
        color = offline

    return f"{color}{value}{Style.RESET_ALL}"


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

# Function to convert bytes to appropriate unit
def convert_from_bytes(total_bytes):
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    while total_bytes >= 1024 and unit_index < len(units) - 1:
        total_bytes /= 1024
        unit_index += 1
    return f'{total_bytes:.2f} {units[unit_index]}'

# Function to convert units to bytes for summation
def convert_to_bytes(value, unit):
    units = {
        'KB': 1024,
        'MB': 1024 ** 2,
        'GB': 1024 ** 3,
        'TB': 1024 ** 4,
        'PB': 1024 ** 5
    }
    return float(value) * units[unit]

class Terminal:
    def print_Node_Details(node):
        name = str(node.name)
        current_total = str(node.current_total)
        estimated_total = str(node.estimated_total)
        disk_used = str(node.disk_used)
        unpaid_data = str(node.unpaid_data)
        deviation_warning = ""
        uptime = colored_value(str(node.uptime))

        # Check if deviation_percentage is set and format the warning string with ANSI color codes
        if str(node.deviation_percentage):
            deviation_warning = f"\033[31m Report Deviation: {str(node.deviation_percentage)}\033[0m"

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
        print("┌─────────────────── NODE MAIN STATS ────────────────────┐┌─────────────── FILEWALKER ────────────────┐")
        print("│                                                        ││                                           │")
        print("│ Current Total: {:>9} $        Uptime: {:>8}     ││       GARBAGE     TRASH       USED SPACE  │".format(current_total, pad_with_color(uptime, 8)))
        print("│ Estimated Total: {:>7} $                             ││       COLLECTOR   CLEANUP     FILEWALKER  │".format(estimated_total))
        print("│                                                        ││                                           │")
        print("│ Disk Used: {:>15}                             ││   SL  {:21}{:21}{:20} │".format(disk_used, gcf_sl, tcf_sl, usf_sl))
        print("│ Unpaid Data: {:>13}                             ││  AP1  {:21}{:21}{:20} │".format(unpaid_data, gcf_ap1, tcf_ap1, usf_ap1))
        print("│                                                        ││  EU1  {:21}{:21}{:20} │".format(gcf_eu1, tcf_eu1, usf_eu1))
        print("│{:>28}                            ││  US1  {:21}{:21}{:20} │".format(pad_with_color(deviation_warning, 28), gcf_us1, tcf_us1, usf_us1))
        print("│                                                        ││                                           │ ")
        print("└────────────────────────────────────────────────────────┘└───────────────────────────────────────────┘ ")

    def print_Summary(nodes):
        summed_current_total = 0
        summed_estimated_total = 0
        summed_disk_used = 0
        summed_unpaid_data = 0


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
            # Sum up "current total"
            summed_current_total += float(node.current_total)

            # Sum up "estimated total"
            summed_estimated_total += float(node.estimated_total)

            # Sum up "disk used"
            disk_value, disk_unit = node.disk_used.split()
            summed_disk_used += convert_to_bytes(disk_value, disk_unit)

            # Sum up "unpaid data"
            unpaid_value, unpaid_unit = node.unpaid_data.split()
            summed_unpaid_data += convert_to_bytes(unpaid_value, unpaid_unit)

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

        summed_disk_used = str(convert_from_bytes(summed_disk_used))
        summed_unpaid_data = str(convert_from_bytes(summed_unpaid_data))

        print("")
        print("")
        print("═════════════════════════════════════════ All Nodes - Summary ═════════════════════════════════════════")
        print("")
        print("┌─────────────────── NODE MAIN STATS ────────────────────┐┌─────────────── FILEWALKER ────────────────┐")
        print("│                                                        ││                                           │")
        print("│ Current total:    {:6.2f} $                             ││       GARBAGE     TRASH       USED SPACE  │".format(summed_current_total))
        print("│ Estimated total:  {:6.2f} $                             ││       COLLECTOR   CLEANUP     FILEWALKER  │".format(summed_estimated_total))
        print("│                                                        ││                                           │")
        print("│ Disk used: {:>15}                             ││   SL  {:12}{:12}{:11} │".format(summed_disk_used, gcf[Satellite.SL], tcf[Satellite.SL], usf[Satellite.SL]))
        print("│ Unpaid Data: {:>13}                             ││  AP1  {:12}{:12}{:11} │".format(summed_unpaid_data, gcf[Satellite.AP1], tcf[Satellite.AP1], usf[Satellite.AP1]))
        print("│                                                        ││  EU1  {:12}{:12}{:11} │".format(gcf[Satellite.EU1], tcf[Satellite.EU1], usf[Satellite.EU1]))
        print("│                                                        ││  US1  {:12}{:12}{:11} │".format(gcf[Satellite.US1], tcf[Satellite.US1], usf[Satellite.US1]))
        print("│                                                        ││                                           │ ")
        print("└────────────────────────────────────────────────────────┘└───────────────────────────────────────────┘ ")


class Node:
    def __init__(self, name, log_dir, db_path, earnings_calculator):
        self.name = name
        self.log = ""
        self.earnings = ""
        self.current_total = ""
        self.is_up = False
        self.estimated_total = ""
        self.disk_used = ""
        self.unpaid_data = ""
        self.deviation_percentage = ""
        self.uptime = ""

        self.usf = {sat: "unknown" for sat in Satellite}
        self.gcf = {sat: "unknown" for sat in Satellite}
        self.tcf = {sat: "unknown" for sat in Satellite}

        self.usf_set = {sat: False for sat in Satellite}
        self.gcf_set = {sat: False for sat in Satellite}
        self.tcf_set = {sat: False for sat in Satellite}

        self.read_log(log_dir)
        self.run_earnings_calculator(db_path, earnings_calculator)
        self.parse_earnings()

    def read_log(self, log_dir):
        log_files = glob.glob(os.path.join(log_dir, "*"))
        log_files.sort(key=os.path.getmtime, reverse=True)

        sys.stdout.write(f'\r[INFO] Processing {self.name}\n')
        sys.stdout.flush()

        for log_file in log_files:
            with open(log_file, 'rb') as f:
                sys.stdout.write(f'\r[ ~~ ] Reading {log_file}')
                sys.stdout.flush()

                data = f.read()
                lines = data.split(b'\n')
                lines.reverse()

                for line in lines:
                    line = line.decode('utf-8')
                    self.process_log_line(line)

                    if self.is_up:
                        sys.stdout.write(f'\r[ OK ] {log_file} read                                             \n')
                        sys.stdout.flush()
                        break
                else:
                    sys.stdout.write(f'\r[ OK ] {log_file} read                                             \n')
                    sys.stdout.flush()
                    continue

            break

    def process_log_line(self, line):
        if " Got a signal from the OS: \"terminated\"" in line:
            self.is_up = True
            self.uptime = "offline"
            self.set_offline()
            return True
        if "emptying" in line:
            self.parse_tcf_line(line)
        elif "retain" in line:
            self.parse_gcf_line(line)
        elif "used-space-filewalker" in line:
            self.parse_usf_line(line)
        elif "Configuration loaded" in line:
            self.is_up = True
            self.set_uptime(line)
            return True
        return False

    def set_offline(self):
        self.usf = {sat: "offline" for sat in Satellite}
        self.gcf = {sat: "offline" for sat in Satellite}
        self.tcf = {sat: "offline" for sat in Satellite}

    def set_uptime(self, line):
        timestamp_str = line[:25]
        time = self.parse_timestamp(timestamp_str)
        time_utc = time.astimezone(timezone.utc)
        current_time_utc = datetime.now(timezone.utc)
        uptime = current_time_utc - time_utc
        days, hours = uptime.days, uptime.seconds // 3600
        self.uptime = f'{days}d {hours}h'

    def parse_timestamp(self, timestamp_str):
        try:
            return datetime.fromisoformat(timestamp_str)
        except ValueError:
            time = datetime.strptime(timestamp_str[:19], '%Y-%m-%dT%H:%M:%S')
            return time.replace(tzinfo=timezone.utc)

    def run_earnings_calculator(self, db_path, earnings_calculator):
        try:
            sys.stdout.write(f'\r[ ~~ ] Running earnings calculator for {self.name}\r')
            sys.stdout.flush()
            
            self.earnings = subprocess.run([sys.executable, earnings_calculator, db_path], capture_output=True, text=False)
            self.earnings.stdout = self.earnings.stdout.decode('utf-8')
            
            sys.stdout.write(f'\r[ OK ] Running earnings calculator for {self.name}\n')
            sys.stdout.flush()
        except subprocess.SubprocessError:
            sys.exit("ERROR: Could not run earnings calculator")

    def parse_earnings(self):
        if self.earnings.stdout.splitlines() == []:
            print("[WARN] Output of earnings calculator is empty. Check if your config (earnings calculator) is correct!")
            return
        try:
            print()
            for line in self.earnings.stdout.splitlines():
                try:
                    if "Total\t\t\t\t\t" in line:
                        self.current_total = self.extract_last_value(line)
                    if "Estimated total" in line:
                        self.estimated_total = self.extract_last_value(line)
                    if "Disk Current Total" in line:
                        self.disk_used = self.extract_value_with_unit(line)
                    if "Total Unpaid Data <─" in line:
                        self.unpaid_data = self.extract_value_with_unit(line)
                    if "Disk Last Report deviates" in line:
                        self.deviation_percentage = self.extract_percentage(line)
                except Exception as e:
                    print(f"Error processing line: {line}")
                    logging.error(traceback.format_exc())
        except Exception as e:
            print("Invalid earnings calculator output. Check if earnings calculator is working.")
            logging.error(traceback.format_exc())

    def extract_last_value(self, line):
        return line.split()[-1]

    def extract_value_with_unit(self, line):
        parts = line.split()
        return f'{parts[-2]} {parts[-1]}'

    def extract_percentage(self, line):
        import re
        match = re.search(r'\b\d+(\.\d+)?%', line)
        return match.group(0) if match else "0%"

    def parse_tcf_line(self, line):
        self.parse_satellite_line(line, self.tcf, self.tcf_set)

    def parse_gcf_line(self, line):
        self.parse_satellite_line(line, self.gcf, self.gcf_set)

    def parse_usf_line(self, line):
        self.parse_satellite_line(line, self.usf, self.usf_set)

    def parse_satellite_line(self, line, status_dict, status_set_dict):
        for sat in Satellite:
            if not status_set_dict[sat]:
                if "finished" in line and sat.value in line:
                    status_dict[sat] = self.parse_date_and_time(line)
                    status_set_dict[sat] = True
                elif "completed" in line and sat.value in line:
                    status_dict[sat] = self.parse_date_and_time(line)
                    status_set_dict[sat] = True
                elif "Moved" in line and sat.value in line:
                    status_dict[sat] = self.parse_date_and_time(line)
                    status_set_dict[sat] = True
                elif "started" in line and sat.value in line:
                    status_dict[sat] = "running"
                elif "Prepared" in line and sat.value in line:
                    status_dict[sat] = "running"

    def parse_date_and_time(self, line):
        timestamp_str = line[:25]
        time = self.parse_timestamp(timestamp_str)
        time_utc = time.astimezone(timezone.utc)
        current_time_utc = datetime.now(timezone.utc)
        time_difference = current_time_utc - time_utc
        days, hours = time_difference.days, time_difference.seconds // 3600
        return f'{days}d {hours}h ago'
        

class Satellite(Enum):
    SL  = "1wFTAgs9DP5RSnCqKV1eLf6N9wtk4EAtmN5DpSxcs8EjT69tGE"
    AP1 = "121RTSDpyNZVcEU84Ticf2L1ntiuUimbWgfATz21tuvgk3vzoA6"
    US1 = "12EayRS2V1kEsWESU9QMRseFhdxYxKicsiFmxrsLZHeLUtdps3S"
    EU1 = "12L9ZFwhzVpuEKMUNUqkaTLGzwY9G24tbiigLiXpmZWKwmcNDDs"


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        init()  # Windows needs initialization of colorama
    main()
