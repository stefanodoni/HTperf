# HTperf
A framework composed by two tools:
 - LaunchCollectors.py automates the collection of performance data using ocperf and sar.
 - Main.py automates the parsing, selection, aggregation and plotting processes of data from csv files reported by tools like Sar, PCM, perf and benchmarks like RUBBoS and SPECpower.

## Usage
Execute LaunchCollectors.py passing as arguments the Sar Interval and Count parameters, the ocperf directory and the output directory.
```sh
$ ./LaunchCollectors.py interval count /path/to/pmu-tools /path/to/output/dir
```

Execute main.py passing as arguments the path of directory containing the reports of each test under consideration and the output directory.
Each reporting directory must contains these csv files:

 - perf.csv: report of perf tool
 - sar.csv: report of sar tool
 - benchmark.csv : report of benchmark

```sh
$ ./main.py /path/to/report/dir /path/to/output/dir
```

Optional parameters are:

 - -pcm: parse the pcm.csv (report of Intel PCM tool) file placed in report directory
 - -sysconfig: parse the single sysConfig.csv file placed in the root of reports directory

```sh
$ ./main.py /path/to/report/dir /path/to/output/dir -sysconfig -pcm
```

## Benchmark report file structure
The file benchmark.csv must have the following column structure:

| Timestamp Start | Timestamp End | Run # | Tot Clients | Tot Avg X | Tot Avg R | Tot Avg U |
| --------------- | ------------- | ----- | ----------- | --------- | --------- | --------- |
| YYYY-MM-DD HH:mm:ss | YYYY-MM-DD HH:mm:ss | n | k | x | r | u |
| 2016-1-26 23:23:31 | 2016-1-26 23:26:31 | 1 | 840 | 131 | 2 | 12.0975 |