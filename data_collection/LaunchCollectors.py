import os
import shlex
import subprocess
import argparse
import getpass

__author__ = 'francesco'

parser = argparse.ArgumentParser(description='LaunchCollectors tool: starts ocperf and sar tools, stops them and converts files.')
parser.add_argument('interval', metavar='interval', help='sampling interval')
parser.add_argument('count', metavar='count', help='sampling count')
parser.add_argument('pmutoolsdirpath', metavar='pmutoolsdirpath', help='path to pmu-tools directory, which contains ocperf tool')
parser.add_argument('reportdirpath', metavar='reportdirpath', help='path to directory in which the tool generates the reports')
args = parser.parse_args()

# Get the chosen output dir and create it if necessary
OUTPUT_DIR = os.path.join(args.reportdirpath, '')
os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)

pmutoolsPath = os.path.join(args.pmutoolsdirpath, '')

# Parameters
# ocperfPath = '/home/francesco/Scrivania/pmu-tools/'
interval = args.interval
count = args.count # Total sar duration is sarInterval * sarCount seconds

perfLog = OUTPUT_DIR + 'perf.csv'
sarLog = OUTPUT_DIR + 'sar.log'
sarCsv = OUTPUT_DIR + 'sar-client0.csv'

# Remove old files if present
try:
    os.remove(perfLog)
    os.remove(sarLog)
    os.remove(sarCsv)
except OSError:
    pass

# Start ocperf and sar tools
print('Start monitoring ... ')
cmd = 'sudo ' + pmutoolsPath + 'ocperf.py stat -e instructions,cpu_clk_unhalted.thread,cpu_clk_unhalted.thread_any,cpu_clk_unhalted.ref_tsc -a -A -x ";" -o ' + perfLog \
+ ' -I ' + str(int(interval)*1000) \
+ ' sleep ' + str(int(count)*int(interval))

args = shlex.split(cmd)
ocperfProcess = subprocess.Popen(args, stdout=subprocess.DEVNULL)

cmd = 'sar -u ' + interval + ' ' + count + ' -o ' + sarLog
args = shlex.split(cmd)
sarProcess = subprocess.Popen(args, stdout=subprocess.DEVNULL)

sarProcess.wait()
#if sarProcess.wait() == 0: # Wait for sar to finish, then kill ocperf and perf processes
#	finish=1
#    os.system("sudo killall perf")

print("Finished monitoring!")

# Generate csv files
print("Start converting sar file ... ", end="")

sarFile = open(sarCsv, 'w')

cmd = 'sadf -dt  ' + sarLog
args = shlex.split(cmd)
sarProcess = subprocess.Popen(args, stdout=sarFile)

print('done!')

# Get username
username = getpass.getuser()

# Change file owner
cmd = 'sudo chown ' + username + ' ' + perfLog
args = shlex.split(cmd)
chownProcess = subprocess.Popen(args)
