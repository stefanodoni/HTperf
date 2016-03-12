#!/bin/bash
#Dare in ingresso allo script la directory dei risultati del benchmark
echo "Before launching this script you should change its hard-coded values."
echo "Call this script passing as argument the path to directory containing RUBBoS results."

data=`date +%Y-%m-%d@%H:%M:%S`
numClientNodes=2 #Modificare se vengono definiti più client in RUBBoS
reportOut=$1/report-$data.csv
echo "STARTING"
echo "Timestamp Start;Timestamp End;Run #;Tot Clients;Tot Avg X;Tot Avg R;Tot Avg U;"  > $reportOut

runNumber=1
dirNumber=1

#for benchDir in $*;
for benchDir in `find $1 -mindepth 1 -type d | sort -V`;
do
	tsStartGlob=''
	tsEndGlob=''
	totX=0
	totR=0
	totU=0

	#Estraggo numero di client della run
	clientsNumber=`perl -ne 'print $1, "\n" if /Number of clients.+: ([0-9]+)<br>$/' $benchDir/index.html`
	
	for (( i = 0 ; i < $numClientNodes ; i += 1 )) ;
	do
		statClient=$benchDir/stat_client$i.html
		echo $statClient

		#Controllo che esista il file, altrimenti esco
		[ -f $statClient ] || {
			echo "ERRORE"
			break
		}

		#Genero i csv dei file di sar
		sadf -dt $benchDir/client$i.bin > $benchDir/client$i.csv

		#Genero un unico csv di sar per ogni client
		sadf -dt $benchDir/client$i.bin >> $1/sar-client-$i-report-$data.csv

		#Estraggo avg X e avg R
		rubbos_perf=(`awk '/<br><h3>Runtime session statistics<\/h3><p>/,/Average throughput/' $statClient | perl -ne 'print $1, "\n" if /Average throughput.+<B>([0-9]+)/ ; print "$1 " if /Total.+?([0-9]+) ms/'`)

		X=${rubbos_perf[1]}
		R=${rubbos_perf[0]}

		totX=$(($totX + ${rubbos_perf[1]}))
		totR=$(($totR + ${rubbos_perf[0]}))

		# Fix rubbos date formats, inserting leading zeroes when needed
		sed -e 's/ \([0-9]\):/ 0\1:/' -e 's/:\([0-9]\):/:0\1:/' -e 's/:\([0-9]\)$/:0\1/' $statClient > $statClient.sed

		#Timestamp inizio
		tsStart=`perl -ne 'print $1, "\n" if /Runtime session start.+<TD>(.+)$/' $statClient.sed`

		#Timestamp fine
		tsEnd=`perl -ne 'print $1, "\n" if /Down ramp start.+<TD>(.+)$/' $statClient.sed`

		if [[ $i -eq 0 ]] ; then
			tsStartGlob=$tsStart
			tsEndGlob=$tsEnd
		fi

		#Orario inizio Session
		sessionStart=`perl -ne 'print $1, "\n" if /Runtime session start.+<TD>.+ ([0-9]+:[0-9]+:[0-9]+)$/' $statClient.sed`

		#Orario inizio Down Ramp
		sessionEnd=`perl -ne 'print $1, "\n" if /Down ramp start.+<TD>.+ ([0-9]+:[0-9]+:[0-9]+)$/' $statClient.sed`

		echo "Parsing run: $sessionStart -> $sessionEnd"
		echo "Processing client: $i"
		echo -n "Calculating CPU utilization ..."		

		#Calcolo Average Utilization nell'intervallo della Session
		U=`sadf -dt $benchDir/client$i.bin -s $sessionStart -e $sessionEnd -- -u | sed 's/,/./g' | awk -F';' '{totUser+=$5 ; totNice+=$6 ; totSystem+=$7 ; count+=1} ; END {print (totUser+totNice+totSystem)/count}'`
		echo " got: $U. done"
		
		totU=`echo $totU + $U | bc` # float add
	done

	#Stampo la riga complessiva della run $runNumber
	echo "$tsStartGlob;$tsEndGlob;$runNumber;$(($clientsNumber * 2));$totX;$(($totR / $numClientNodes));`echo "$totU / $numClientNodes" | bc -l`;"  >> $reportOut
	
	#Incremento il contatore della run se arrivo alla decima cartella e riparto da uno
	if [[ $dirNumber -eq 10 ]] ; then
		runNumber=$(($runNumber + 1))
		dirNumber=1
	else
		dirNumber=$(($dirNumber + 1))
	fi
done
