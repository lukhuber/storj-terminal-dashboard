# Storj Terminal Dashboard
Storj Terminal Dashboard serves as a utility to monitor and display the operational health and financial performance of Storj nodes in a terminal-based dashboard. Its most useful function is to display the current status of all Filewalkers of the individual nodes in a clear and easily understandable way.

It uses [René Smeekes](https://github.com/ReneSmeekes)'s [storj_earnings](https://github.com/ReneSmeekes/storj_earnings) script to pull financial and disk storage data. 

![Screenshot of the storj terminal dashboard](https://github.com/lukhuber/storj-terminal-dashboard/blob/main/images/screenshot.png?raw=true)

## Prerequisites
Python 3.2 or newer is required in order to run this script. 
It was tested on Linux with Python 3.12. Other operating systems are likely to also work.

[This storj_earnings](https://github.com/ReneSmeekes/storj_earnings) script is required.

### Warning
As the [storj_earnings](https://github.com/ReneSmeekes/storj_earnings) script is invoked when using this dashboard, all limitations and precautions of it also apply. Please refer to the information about running the script in its respective repository.

This script loads the log files individually into RAM. Make sure that you have more free RAM than your largest log file before executing the script.

## Usage
Adjust the respective paths to the logs and databases of each node in <code>storj-dashboard.json</code>. Note that the log path must be specified up to the file. The database path only needs to be specified up to the containing folder. 

You must also specify the storage path to the storj-earnings script.

To start the script, simply run it:
```
./storj-dashboard.py
```

Optionally, you can use multiple different config files if you want. This is useful, if you want to display different subsets of you nodes. Just add the path to the config file after the command:
```
./storj-dashboard.py <path/to/config.json>
```