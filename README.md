# HTperf
A framework composed by two tools:
- Main.py automates the parsing, selection, aggregation and plotting processes of data from csv files reported by tools like Sar, PCM, perf and benchmarks like RUBBoS and SPECpower.
- LaunchCollectors.py automates the collection of performance data using ocperf and sar.

Execute main.py passing as arguments the directory path containing the reports of each test under consideration and the output directory. Each reporting directory must contains these csv files: perf.csv, rubbos.csv and sar-client0.csv. Add "-pcm" argument in order to parse the pcm.csv file.

Execute LaunchCollectors.py passing as arguments the Sar Interval and Count parameters, the ocperf directory and the output directory.
