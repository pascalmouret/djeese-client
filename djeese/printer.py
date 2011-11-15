# -*- coding: utf-8 -*-


class Printer(object):
    """
    Helper object to print certain types of information only if the verbosity
    level given is high enough.
    """
    def __init__(self, verbosity):
        self.verbosity = verbosity
    
    def _print(self, level, message):
        if self.verbosity >= level:
            print message
    
    def info(self, message):
        """
        Print if verbosity is 3 or above
        """
        self._print(3, message)
    
    def warning(self, message):
        """
        Print if verbosity is 2 or above
        """
        self._print(2, message)
    
    def error(self, message):
        """
        Print if verbosity is 1 or above
        """
        self._print(1, message)
        
    def always(self, message):
        self._print(-1, message)
    