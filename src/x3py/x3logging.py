#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# *************************************************************************** #
#                  Copyright © 2022, UChicago Argonne, LLC                    #
#                           All Rights Reserved                               #
#                         Software Name: Tomocupy                             #
#                     By: Argonne National Laboratory                         #
#                                                                             #
#                           OPEN SOURCE LICENSE                               #
#                                                                             #
# Redistribution and use in source and binary forms, with or without          #
# modification, are permitted provided that the following conditions are met: #
#                                                                             #
# 1. Redistributions of source code must retain the above copyright notice,   #
#    this list of conditions and the following disclaimer.                    #
# 2. Redistributions in binary form must reproduce the above copyright        #
#    notice, this list of conditions and the following disclaimer in the      #
#    documentation and/or other materials provided with the distribution.     #
# 3. Neither the name of the copyright holder nor the names of its            #
#    contributors may be used to endorse or promote products derived          #
#    from this software without specific prior written permission.            #
#                                                                             #
#                                                                             #
# *************************************************************************** #
#                               DISCLAIMER                                    #
#                                                                             #
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS         #
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT           #
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS           #
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT    #
# HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,      #
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED    #
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR      #
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF      #
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING        #
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS          #
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.                #
# *************************************************************************** #
"""
Created on Thu Apr 13 12:55:13 2023

@author: amittone
"""

#importing the module 
import logging 
from logging import *
import traceback
#now we will Create and configure logger 
#logging.basicConfig(filename="x3py.log", 
#					format='%(asctime)s %(message)s', 
#					filemode='w') 

#Let us Create an object 
#logger=logging.getLogger() 

#Now we are going to Set the threshold of logger to DEBUG 
#logger.setLevel(logging.DEBUG) 

#some messages to test
#logger.debug("") 
#logger.info("") 
#logger.warning("") 
#logger.error("") 
#logger.critical("") 



__all__ = ['setup_custom_logger', 'ColoredLogFormatter'] + logging.__all__

def log_exception(logger, err, fmt="%s"):
    """Send a reconstructed stacktrace to the log.

    The stacktrace will be sent to the error log for the given logger.

    Parameters
    ==========
    logger
      A logger, as returned by ``logging.getLogger(...)``
    err
      An exception to log.
    fmt
      Logging format string for each line of the exception
      (e.g. "  *** %s"")
    
    """
    tb_lines = traceback.format_exception(type(err), err, err.__traceback__)
    tb_lines = [ln for lns in tb_lines for ln in lns.splitlines()]
    for tb_line in tb_lines:
        logger.error("      %s", tb_line)


def setup_custom_logger(lfname: str=None, stream_to_console: bool=True, level=logging.DEBUG):
    """Prepare the logging system with custom formatting.
    
    This adds handlers to the *tomocupy* parent logger. Any logger
    inside tomocupy will produce output based on this functions
    customization parameters. The file given in *lfname* will receive
    all log message levels, while the console will receive messages
    based on *level*.
    
    Parameters
    ----------
    lfname
      Path to where the log file should be stored. If omitted, no file
      logging will be performed.
    stream_to_console
      If true, logs will be output to the console with color
      formatting.
    level
      A logging level for the stream handler. This can be either a
      string ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"), or an
      actual level defined in the python logging framework.

    """
    parent_name = __name__.split('.')[0]  # Nominally "tomocupy"
    parent_logger = logging.getLogger(parent_name)
    parent_logger.setLevel(logging.DEBUG)
    # Set up normal output to a file
    if lfname is not None:
        fHandler = logging.FileHandler(lfname)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s(%(lineno)s) - %(levelname)s: %(message)s')
        fHandler.setFormatter(file_formatter)
        fHandler.setLevel(logging.DEBUG)
        parent_logger.addHandler(fHandler)
    # Set up formatted output to the console
    if stream_to_console:
        ch = logging.StreamHandler()
        ch.setFormatter(ColoredLogFormatter('%(asctime)s - %(message)s'))
        ch.setLevel(level)
        parent_logger.addHandler(ch)

class ColoredLogFormatter(logging.Formatter):
	"""A logging formatter that add console color codes."""
	__BLUE = '\033[94m'
	__GREEN = '\033[92m'
	__RED = '\033[91m'
	__RED_BG = '\033[41m'
	__YELLOW = '\033[33m'
	__ENDC = '\033[0m'

	def _format_message_level(self, message, level):
		colors = {
			'info': self.__GREEN,
			'warning': self.__YELLOW,
			'error': self.__RED,
			'critical': self.__RED_BG,
		}
		if level in colors.keys():
			message = "{color}{message}{ending}".format(color=colors[level],
														message=message,
														ending=self.__ENDC)
		return message

	def formatMessage(self, record):
		record.message = self._format_message_level(record.message, record.levelname)
		return super().formatMessage(record)
