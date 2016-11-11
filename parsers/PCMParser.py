import pandas as pd
from parsers.Parser import Parser


class PCMParser (Parser):
    columns = ['SysDate', 'SysTime', 'SysEXEC', 'SysIPC', 'SysFREQ',
    'SysAFREQ', 'SysL3MISS', 'SysL2MISS', 'SysL3HIT', 'SysL2HIT',
    'SysL3MPI', 'SysL2MPI', 'SysREAD', 'SysWRITE', 'SysINST',
    'SysACYC', 'SysTIMEticks', 'SysPhysIPC', 'SysPhysIPCPerc', 'SysINSTnom', 'SysINSTnomPerc',
    'SysCoreCStatesC0res', 'SysCoreCStatesC1res', 'SysCoreCStatesC3res', 'SysCoreCStatesC6res', 'SysCoreCStatesC7res',
    'SysPackCStatesC2res', 'SysPackCStatesC3res', 'SysPackCStatesC6res', 'SysPackCStatesC7res', 'SysPackCStatesProcEnergy',
    'SKT0EXEC', 'SKT0IPC', 'SKT0FREQ', 'SKT0AFREQ', 'SKT0L3MISS',
    'SKT0L2MISS', 'SKT0L3HIT', 'SKT0L2HIT', 'SKT0L3MPI', 'SKT0L2MPI',
    'SKT0READ','SKT0WRITE', 'SKT0TEMP',
    'SKT0CoreCStateC0res', 'SKT0CoreCStateC1res', 'SKT0CoreCStateC3res', 'SKT0CoreCStateC6res', 'SKT0CoreCStateC7res',
    'SKT0PackCStateC2res', 'SKT0PackCStateC3res', 'SKT0PackCStateC6res', 'SKT0PackCStateC7res',
    'ProcEnergySKT0',
    'Core0Sock0EXEC', 'Core0Sock0IPC', 'Core0Sock0FREQ', 'Core0Sock0AFREQ', 'Core0Sock0L3MISS',
    'Core0Sock0L2MISS', 'Core0Sock0L3HIT', 'Core0Sock0L2HIT', 'Core0Sock0L3MPI', 'Core0Sock0L2MPI',
    'Core0Sock0C0res', 'Core0Sock0C1res', 'Core0Sock0C3res', 'Core0Sock0C6res', 'Core0Sock0C7res', 'Core0Sock0TEMP',
    'Core1Sock0EXEC', 'Core1Sock0IPC', 'Core1Sock0FREQ', 'Core1Sock0AFREQ', 'Core1Sock0L3MISS',
    'Core1Sock0L2MISS', 'Core1Sock0L3HIT', 'Core1Sock0L2HIT', 'Core1Sock0L3MPI', 'Core1Sock0L2MPI',
    'Core1Sock0C0res', 'Core1Sock0C1res', 'Core1Sock0C3res', 'Core1Sock0C6res', 'Core1Sock0C7res', 'Core1Sock0TEMP',
    'Core2Sock0EXEC', 'Core2Sock0IPC', 'Core2Sock0FREQ', 'Core2Sock0AFREQ', 'Core2Sock0L3MISS',
    'Core2Sock0L2MISS', 'Core2Sock0L3HIT', 'Core2Sock0L2HIT', 'Core2Sock0L3MPI', 'Core2Sock0L2MPI',
    'Core2Sock0C0res', 'Core2Sock0C1res', 'Core2Sock0C3res', 'Core2Sock0C6res','Core2Sock0C7res', 'Core2Sock0TEMP',
    'Core3Sock0EXEC', 'Core3Sock0IPC', 'Core3Sock0FREQ', 'Core3Sock0AFREQ', 'Core3Sock0L3MISS',
    'Core3Sock0L2MISS', 'Core3Sock0L3HIT', 'Core3Sock0L2HIT', 'Core3Sock0L3MPI', 'Core3Sock0L2MPI',
    'Core3Sock0C0res', 'Core3Sock0C1res', 'Core3Sock0C3res', 'Core3Sock0C6res', 'Core3Sock0C7res', 'Core3Sock0TEMP']

    def parse(self, file):
        csvfile = open(file, 'rb')
        dataframe = pd.read_csv(csvfile, sep=';', header=None, skiprows=2,
                                names=self.columns, decimal='.', index_col=False,
                                parse_dates={Parser.TIMESTAMP_STR: [0, 1]},
                                date_parser = lambda x: pd.datetime.strptime(x, '%Y-%m-%d %H:%M:%S.%f'))

        csvfile.close()
        return dataframe
