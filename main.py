import sys
from parsers.SarParser import SarParser

__author__ = 'francesco'

if len(sys.argv) < 2:
    print("Need sar csv file param!")
    sys.exit()

dataset = SarParser().parse(sys.argv[1])
SarParser().printDiag(dataset)
