# -*- coding: utf-8 -*-


class Printer(object):
    def __init__(self, verbosity):
        self.verbosity = verbosity
    
    def _print(self, level, message):
        if self.verbosity >= level:
            print message
    
    def info(self, message):
        self._print(3, message)
    
    def warning(self, message):
        self._print(2, message)
    
    def error(self, message):
        self._print(1, message)
    