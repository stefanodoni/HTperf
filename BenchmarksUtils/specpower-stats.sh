#!/bin/bash
# First param is path to result dir, second param is desired output directory
echo "Call this script passing as arguments:"
echo "1- the path to directory containing SPECpower results"
echo "2- the path to the desired output directory"

reportOut=$2/stats-report.csv

echo -n "STARTING SPECpower stats computation ..."
echo "Timestamp Start;Timestamp End;Run #;Tot Clients;Tot Avg X (ssj_ops);Tot Avg R (ms);Tot Avg U;" > $reportOut

runNumber=1
for benchDir in `find $1 -mindepth 1 -type d | sort -V`;
do
	cd $benchDir
	resultFile=`find -regex .*[0-9]+.results | sed 's/\.\///'` # Get file ssj.NUMBER.MACHINE.NUMBER.results

	actualOps=(`perl -ne 'print $1,"\n" if /Actual ops.+ ([0-9]+)\.[0-9]+ ssj/' $benchDir/$resultFile`)
	actualLoad=(`perl -ne 'print $1,"\n" if /Actual ops.+ \( *([0-9]+\.[0-9]+)% of/' $benchDir/$resultFile`)
	avgProcessingTime=(`perl -ne 'print $1,"\n" if /Txn Batches.+ ([0-9]+\.[0-9]+)/' $benchDir/$resultFile | sed 's/\.//' | sed 's/0*//'`)

	j=-1
	for i in {1..10};
	do
		tsStart=`perl -ne 'print $1 if /'$i'0% measure.+began at (.*) for/' $benchDir/$resultFile`
		tsStart=`date -d "$tsStart" +'%Y-%m-%d %H:%M:%S'`

		tsEnd=`perl -ne 'print $1 if /'$i'0% post-measure.+began at (.*) for/' $benchDir/$resultFile`
		tsEnd=`date -d "$tsEnd" +'%Y-%m-%d %H:%M:%S'`

		X=${actualOps[$j]} # Skip first 3 elements (that are calibration values)
		R=${avgProcessingTime[$j]}
		U=${actualLoad[$j]}
		j=$((j - 1))

		echo "$tsStart;$tsEnd;$runNumber;1;$X;$R;$U;" >> $reportOut
	done
	runNumber=$((runNumber + 1))
done
echo " done!"
