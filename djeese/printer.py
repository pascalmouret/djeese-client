# -*- coding: utf-8 -*-
from __future__ import with_statement
import os

LEVELS = {
    4: 'LOG',
    3: 'INFO', 
    2: 'WARNING', 
    1: 'ERROR',
    -1: 'CRITICAL',
}

class Printer(object):
    """
    Helper object to print certain types of information only if the verbosity
    level given is high enough.
    """
    def __init__(self, verbosity, logfile=None):
        self.verbosity = verbosity
        self.logfile = open(logfile, 'w') if logfile else open(os.devnull, 'w')
    
    def _print(self, level, message):
        self.logfile.write('[%s]%s\n' % (LEVELS[level], message))
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
    
    def log_only(self, message):
        self._print(4, message)
    