#!/usr/bin/env python3

from argparse import ArgumentParser
from functools import partial
from asyncio import get_event_loop, Future, Queue

from toolrack.script import Script
from toolrack.async import ProcessParserProtocol


class CommandOutputParser:
    '''Parse process output and push parsed samples to a queue.'''

    def __init__(self, loop, queue):
        self._loop = loop
        self._queue = queue

    async def __call__(self, parser):
        '''Run a a process and parse its output using the parser.'''
        future = Future(loop=self._loop)
        parser_func = partial(self._out_parser, parser.parse_line)
        protocol = ProcessParserProtocol(future, out_parser=parser_func)
        transport, _ = await self._loop.subprocess_exec(
            lambda: protocol, *parser.cmdline)
        result = await future
        transport.close()
        await self._queue.put(None)  # To end processing
        return result

    def _out_parser(self, parser_func, line):
        value = parser_func(line)
        if value is not None:
            self._queue.put_nowait(value)


class Collector:
    '''Collect samples from a queue and process them.'''

    def __init__(self, queue, sample_count):
        self._queue = queue
        self._sample_count = sample_count
        self._samples = []

    async def __call__(self, processor):
        '''Process samples from a queue using the processor.'''
        while True:
            sample = await self._queue.get()
            if sample is None:
                self._process_pending_samples(processor)
                return
            self._samples.append(sample)
            if len(self._samples) == self._sample_count:
                self._process_pending_samples(processor)

    def _process_pending_samples(self, processor):
        '''Process the list of pending samples.'''
        samples, self._samples = self._samples, []
        if samples:
            processor.process(samples)


class ProcessParser:
    '''Parse a process output line by line.'''

    cmdline = ['vmstat', '1']
    #cmdline = ['sudo', 'perf', 'stat', '-I', '1000', '-aAe', 'cycles,instructions']

    def parse_line(self, line):
        '''Parse a line of process output.

        It must return the sample to queue.
        '''

        tokens = line.split()
        try:
            return int(tokens[3])
        except ValueError:
            pass

class SampleProcessor:
    '''Process samples.'''

    def process(self, samples):
        '''Process a list of samples.'''
        print(float(sum(samples)) / len(samples))


class AggregatorScript(Script):

    def get_parser(self):
        parser = ArgumentParser(
            description='Parse process output and aggregate samples.')
        parser.add_argument(
            '-c', '--sample-count', type=int, default=5,
            help='number of samples to aggregate')
        return parser

    def main(self, args):
        loop = get_event_loop()
        loop.run_until_complete(self._main(loop, args))
        loop.close()

    async def _main(self, loop, args):
        queue = Queue(loop=loop)
        parser = CommandOutputParser(loop, queue)
        collector = Collector(queue, args.sample_count)
        task = loop.create_task(collector(SampleProcessor()))
        await parser(ProcessParser())
        await task


if __name__ == '__main__':
    script = AggregatorScript()
    script()
