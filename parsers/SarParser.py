from Parser import Parser

__author__ = 'francesco'

class SarParser (Parser):
    valore = 0

    def __init__(self, value):
        Parser.__init__(self, value)
        print("init sarParser " + str(self.valore))

    def hello(self, valore):
        print("{} sono figlio").format(valore)
