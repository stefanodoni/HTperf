import os
import shlex
import subprocess

__author__ = 'francesco'

# Parameters
ocperfPath = '/home/francesco/Scrivania/pmu-tools/'
sarInterval = '5' # Get stats on a 5 seconds interval
sarCount = '2' # Get stats 2 times. Total sar duration is sarInterval * sarCount seconds

perfLog = 'perf.csv'
sarLog = 'sar.log'
sarCsv = 'sar-client0.csv'

# Remove old files if present
try:
    os.remove(perfLog)
    os.remove(sarLog)
    os.remove(sarCsv)
except OSError:
    pass

# Start ocperf and sar tools
print('Start monitoring ... ')
cmd = 'sudo ' + ocperfPath + 'ocperf.py stat -e instructions,cpu_clk_unhalted.thread,cpu_clk_unhalted.thread_any,cpu_clk_unhalted.ref_tsc -a -A -x ";" -o ' + perfLog + ' -I 1000'
args = shlex.split(cmd)
ocperfProcess = subprocess.Popen(args, stdout=subprocess.DEVNULL)

cmd = 'sar -u ' + sarInterval + ' ' + sarCount + ' -o ' + sarLog
args = shlex.split(cmd)
sarProcess = subprocess.Popen(args, stdout=subprocess.DEVNULL)

if sarProcess.wait() == 0: # Wait for sar to finish, then kill ocperf and perf processes
    os.system("sudo killall perf")

print("Finished monitoring!")

# Generate csv files
print("Start converting sar file ... ", end="")

sarFile = open(sarCsv, 'w')

cmd = 'sadf -dt  ' + sarLog
args = shlex.split(cmd)
sarProcess = subprocess.Popen(args, stdout=sarFile)

print('done!')

# Change file owner
cmd = 'sudo chown francesco ' + perfLog
args = shlex.split(cmd)
chownProcess = subprocess.Popen(args)