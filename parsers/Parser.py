__author__ = 'francesco'

class Parser:
    valore = 0

    def __init__(self, value):
        self.valore = value
        print("init parser " + str(self.valore))

    def hello(self, valore):
        print(valore, "sono padre")