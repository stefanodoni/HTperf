#!/bin/bash
# Manually start ./runtemp.sh, ./runpower.sh and ./runssj.sh in three different terminal windows, then execute this script
echo "Warning: before launching this script, you have to manually execute in three different command lines these SPECpower scripts:"
echo "1- ./runtemp.sh"
echo "2- ./runpower.sh"
echo "3- ./runssj.sh"

specPowerDirPath='/home/francesco/SPECpower'
collectorsDirPath='/home/francesco/PycharmProjects/HTperf/data_collection'
pmuToolsDirPath='/home/francesco/Scrivania/pmu-tools'

date=`date '+%Y-%m-%d@%H:%M:%S'`

reportDirPath=$date-SPECpower

mkdir $reportDirPath

interval=5
#count=960 # 80 min = 1 test
#count=1920 # 160 min = 2 tests
#count=9600 # 800 min = 10 tests
count=9000 # 750 min = 10 tests

# Report current system configuration
echo "System configuration for SPECpower test" > $reportDirPath/system-config.log
echo "Date:" $date >> $reportDirPath/system-config.log
echo "=========== LSCPU OUTPUT: =================" >> $reportDirPath/system-config.log
lscpu >> $reportDirPath/system-config.log
echo "=========== CPUFREQ-INFO OUTPUT: ==========" >> $reportDirPath/system-config.log
cpufreq-info >>  $reportDirPath/system-config.log
echo "=========== PSTATE-FREQUENCY OUTPUT: ======" >> $reportDirPath/system-config.log
pstate-frequency -G >>  $reportDirPath/system-config.log

# Start monitoring
sudo $collectorsDirPath/LaunchCollectors.py $interval $count $pmuToolsDirPath $reportDirPath &

#cd $specPowerDirPath/ptd/
#./runpower.sh > /dev/null 2>&1 &
#./runtemp.sh > /dev/null 2>&1 &
#cd ..

for testNumber in {1..10} ;
#for testNumber in {1..2} ;
do
	echo "Starting test $testNumber"
	date
	cd $specPowerDirPath/ssj/
	./rundirector.sh > /dev/null 2>&1 &
	./runssj.sh > /dev/null 2>&1 &
	cd ..
	cd $specPowerDirPath/ccs/
	./runCCS.sh
	cd ..
	echo "Test ended!"
done

echo "Waiting for monitoring to end data collection ..."
test_ended=0
while [ $test_ended -eq 0 ] ; do
	test_alive=`ps aux | grep sar | grep -v grep`
	[ -z "$test_alive" ] && test_ended=1
	sleep 1		
done
echo "FINISH"
