from parsers.Parser import Parser
import csv


class SysConfigParser (Parser):

    def parse(self, file):
        system_config = {}

        with open(file, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')

            for row in reader:
                try:
                    system_config[row[0]] = float(row[1])
                except ValueError:
                    system_config[row[0]] = row[1]

        return system_config