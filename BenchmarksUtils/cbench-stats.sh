#!/bin/bash
#Dare in ingresso allo script la directory dei risultati del benchmark
echo "Before launching this script you should change its hard-coded values."
echo "Call this script passing as argument the path to directory containing CBench results."

numRequests=3000

reportOut=$1/stats-report.csv
sarOut=$1/sar-client0.csv

echo "STARTING"
echo "Timestamp Start;Timestamp End;Run #;Tot Clients;Tot Avg X (req/s);Tot Avg R (ms);Tot Avg U;"  > $reportOut

for testNumber in {1..10};
do
	for runNumber in {1..10};
	do
		#Run start TS
		tsStart=`perl -ne 'print $3, "\n" if /Start: ([0-9]+) ([0-9]+) ([0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+)$/' $1/logFile-$testNumber-$runNumber.txt`
		timeStart=`echo $tsStart | perl -ne 'print $1, "\n" if /.* ([0-9]+:[0-9]+:[0-9]+)/'`

		#Run end TS
		tsEnd=`perl -ne 'print $3, "\n" if /End: ([0-9]+) ([0-9]+) ([0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+)$/' $1/logFile-$testNumber-$runNumber.txt`
		timeEnd=`echo $tsEnd | perl -ne 'print $1, "\n" if /.* ([0-9]+:[0-9]+:[0-9]+)/'`

		totalSeconds=$(( ( $(date -ud "$tsEnd" +'%s') - $(date -ud "$tsStart" +'%s') ) ))
		#echo "TOT SEC: $totalSeconds"

		#Compute requests completed in order to get the Average Throughput
		completions=`awk '/^#/ {n+=1} ; END {print n}' $1/logFile-$testNumber-$runNumber.txt`

		#Compute Average Response Time
		R=`awk '/^#/ {tot+=$5 ; n+=1} ; END {print tot/n}' $1/logFile-$testNumber-$runNumber.txt`

		echo "Parsing run: $tsStart -> $tsEnd"
		echo -n "Calculating CPU utilization ..."		

		#Compute Average Utilization in given interval
		U=`sadf -dt $1/sarLog-$testNumber-$runNumber.bin -s $timeStart -e $timeEnd -- -u | sed 's/,/./g' | awk -F';' '{totUser+=$5 ; totNice+=$6 ; totSystem+=$7 ; count+=1} ; END {print (totUser+totNice+totSystem)/count}'`
		echo " got: $U. done"

		#Print result line of run $runNumber in csv report
		echo "$tsStart;$tsEnd;$testNumber;$numRequests;$(($completions / $totalSeconds));$R;$U;"  >> $reportOut

		#Append sar results to output file
		sadf -dt $1/sarLog-$testNumber-$runNumber.bin -s $timeStart -e $timeEnd -- -u >> $sarOut
	done	
done
