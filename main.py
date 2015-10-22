import sys
import csv
import numpy as np
import pandas as pd
from parsers.Parser import Parser
from parsers.SarParser import SarParser

__author__ = 'francesco'

if len(sys.argv) < 2:
    print("Need csv file param!")
    sys.exit()

csvfile = open(sys.argv[1], 'rb')
data = pd.read_csv(csvfile, sep=';', header=None, encoding="utf-8-sig") #DataFrame obj
data.set_index('B', inplace=True)
#print(data)

# try:
#     reader = csv.reader(csvfile, delimiter=';')
#     for row in reader:
#         print(", ".join(row))
# finally:
#     csvfile.close()

myParser = Parser(5)
mySarParser = SarParser(4)
mySarParser.hello(54)
print(mySarParser.valore)