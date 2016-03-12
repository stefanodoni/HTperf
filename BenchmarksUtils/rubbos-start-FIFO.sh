#!/bin/bash
#Prima di lanciare lo script, eseguire un comando con sudo (es: sudo date) per inserire la password e poi fare un test di ssh: ssh -x Giglio-pc
echo "Before launching this script you should change its hard-coded values and then execute:"
echo "1- a sudo command (e.g. sudo date) to check if the password is asked or not"
echo "2- an ssh command to test the ssh connection to remote host (e.g. ssh -x hostname)"

runConfigFolder='4200config-F2000-Gpow-FIFO'

date=`date +%Y-%m-%d@%H:%M:%S`

interval=5
pcmLog=PCM-$date.csv
pidstatLog=pidstat-$date.log
perfLog=perf-$date.csv

# Report current system configuration
echo "System configuration for RUBBoS test" $runConfigFolder > system-config.log
echo "Date:" $date >> system-config.log
echo "=========== LSCPU OUTPUT: =================" >> system-config.log
lscpu >> system-config.log
echo "=========== CPUFREQ-INFO OUTPUT: ==========" >> system-config.log
cpufreq-info >>  system-config.log
echo "=========== PSTATE-FREQUENCY OUTPUT: ======" >> system-config.log
pstate-frequency -G >>  system-config.log

# Needed to ensure correct RUBBoS working
sudo date
ssh -x Giglio-pc '
	date
' # In order to exit from remote host

# Initialize Apache2 with FIFO policy
apacheRootProcess=`ps -U root u | grep apache2 | awk 'END {print $2}'`
sudo chrt -f -p 99 $apacheRootProcess
for i in $(pgrep --parent $apacheRootProcess); do sudo chrt -f -p 99 $i; done

# Initialize MySQL with FIFO policy
echo "Initialize MySQL"
echo -n "Stopping MySQL ..."
sudo service mysql stop
echo " done!"
echo -n "Deleting /dev/shm/mysql/ ..."
sudo rm -fR /dev/shm/mysql/
echo " done!"
echo -n "Copying /var/lib/mysql to /dev/shm/mysql..."
sudo cp -pRL /var/lib/mysql /dev/shm/mysql
echo " done!"
echo -n "Starting MySQL ..."
sudo service mysql start
mysqlRootProcess=`ps -U mysql u | grep mysqld | awk 'END {print $2}'`
sudo chrt -f -p 99 $mysqlRootProcess
echo " done!"

sudo /home/francesco/Scrivania/IntelPerformanceCounterMonitor-V2.9/pcm.x $interval -csv=$pcmLog & # Modificare i se cambia la lunghezza del test
pidstat -ru 5 > $pidstatLog &

sudo /home/francesco/Scrivania/pmu-tools/ocperf.py stat -e instructions,cpu_clk_unhalted.thread,cpu_clk_unhalted.thread_any,cpu_clk_unhalted.ref_tsc -a -A -x ";" -o $perfLog -I 1000 &

for i in {1..10} ;
#for i in {1..1} ;
do
	#for f in rubbos.props_0600 rubbos.props_1200 rubbos.props_1800 ;
	for f in $runConfigFolder/rubbos.props*[0-9] ;
	do
		echo "Starting run $i test $f"
		psLog=ps-`date +%Y-%m-%d@%H:%M:%S`.log
		ln -sf $f rubbos.properties       	# questo crea il link al file giusto
		make emulator				# lancia il bench che legge il rubbos.properties

		echo "Waiting for test end ..."		
		test_ended=0
		while [ $test_ended -eq 0 ] ; do
			test_alive=`ps aux | grep stat_client1 | grep -v grep`
			[ -z "$test_alive" ] && test_ended=1
			sleep 1		
		done
		echo "Test ended!"
		ps aux > $psLog
		
		# Restart MySQL in order to avoid memory consumption and tests failure
		echo -n "Stopping MySQL ..."
		sudo service mysql stop
		echo " done!"
		echo -n "Deleting /dev/shm/mysql/ ..."
		sudo rm -fR /dev/shm/mysql/
		echo " done!"
		echo -n "Copying /var/lib/mysql to /dev/shm/mysql..."
		sudo cp -pRL /var/lib/mysql /dev/shm/mysql
		echo " done!"
		echo -n "Starting MySQL ..."
		sudo service mysql start
		mysqlRootProcess=`ps -U mysql u | grep mysqld | awk 'END {print $2}'`
		sudo chrt -f -p 99 $mysqlRootProcess
		echo " done!"
	done
done

echo "Tests ended, closing up ..."

# Kill everything
echo -n "Shutdown processes ..."
sudo killall pcm.x
sudo killall python
sudo killall perf
killall pidstat
echo " done!"

# Change owner of log files
sudo chown francesco $pcmLog $perfLog

# Shutdown MySQL
echo -n "Shutdown MySQL ..."
sudo service mysql stop
echo " done!"
echo -n "Deleting /dev/shm/mysql/ ..."
sudo rm -fR /dev/shm/mysql/
echo " done!"

# Clean up
for f in stat* trace* web* db* client* ; do
	rm /tmp/$f
done

echo "FINISH"
