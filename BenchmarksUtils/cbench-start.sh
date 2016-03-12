#!/bin/bash
echo "Before launching this script you should change its hard-coded values."

runGenFolder='S10msGen-F2000-TB0-FIFO'
runConfigFolder='S10ms-F2000-TB0-FIFO'
cbenchFolder='/home/francesco/Scrivania/cbench'

date=`date '+%Y-%m-%d@%H:%M:%S'`

folder=$date-$runConfigFolder

mkdir $folder

interval=5
pcmLog=$folder/PCM-$date.csv
perfLog=$folder/perf-$date.csv

# Report current system configuration
echo "System configuration for cbench test" $runConfigFolder > $folder/system-config.log
echo "Date:" $date >> $folder/system-config.log
echo "=========== LSCPU OUTPUT: =================" >> $folder/system-config.log
lscpu >> $folder/system-config.log
echo "=========== CPUFREQ-INFO OUTPUT: ==========" >> $folder/system-config.log
cpufreq-info >>  $folder/system-config.log
echo "=========== PSTATE-FREQUENCY OUTPUT: ======" >> $folder/system-config.log
pstate-frequency -G >>  $folder/system-config.log

# Start monitoring local machine only
sudo /home/francesco/Scrivania/IntelPerformanceCounterMonitor-V2.9/pcm.x $interval -csv=$pcmLog &

sudo /home/francesco/Scrivania/pmu-tools/ocperf.py stat -e instructions,cpu_clk_unhalted.thread,cpu_clk_unhalted.thread_any,cpu_clk_unhalted.ref_tsc -a -A -x ";" -o $perfLog -I 1000 &

#for testNumber in {1..10} ;
for testNumber in {1..1} ;
do
	#for f in `ls -v $runConfigFolder/[0-9]*\.txt` ;
	for runNumber in {1..10} ;
	do
		# Generate new sample files from config.lua
		for i in {1..10} ;
		do
			$cbenchFolder/distribgen $runGenFolder/config$i\0.lua > $runConfigFolder/$i\0.txt
		done

		echo "Starting test $testNumber run $runNumber" # $f
		#runNumber=`echo $f | perl -ne 'print $1, "\n" if /.*\/([0-9]+)/'`
		
		> /var/www/html/logFile.txt # empty logFile
		echo "Start: $testNumber $runNumber `date '+%Y-%m-%d %H:%M:%S'`" >> /var/www/html/logFile.txt

		# Monitor one test at a time
		sudo /usr/local/bin/sar -n DEV -n SOCK -rubcw -o $folder/sarLog-$testNumber-$runNumber.bin $interval 0 > /dev/null 2>&1 &

		$cbenchFolder/wcblg ips.txt $runConfigFolder/$runNumber\0.txt > $folder/wcblg-$testNumber-$runNumber.log & # start bench using config file
		sleep 300 # Wait for 300 seconds = 5 minutes that is test length
		sudo killall sar
		sudo killall wcblg

		echo "End: $testNumber $runNumber `date '+%Y-%m-%d %H:%M:%S'`" >> /var/www/html/logFile.txt
		echo "Test ended!"
		
		sudo chown francesco $folder/sarLog-$testNumber-$runNumber.bin
		cp /var/www/html/logFile.txt $folder/logFile-$testNumber-$runNumber.txt
	done
done

echo "Tests ended, closing up ..."

# Kill everything
echo -n "Shutdown processes ..."
sudo killall pcm.x
sudo killall python
sudo killall perf
echo " done!"

# Change owner of log files
sudo chown francesco $pcmLog $perfLog

echo "FINISH"
