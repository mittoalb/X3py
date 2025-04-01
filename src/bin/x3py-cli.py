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
__version__ = "0.0.1"
__author__ = "Alberto Mittone"
__lastrev__ = "Last revision: 04/11/23"

import argparse
import sys

from itkreg import ITKregister
from config import ProInit
import glob
from utils import make_dir, distribute_jobs
import x3logging
	
def main():

	parser = argparse.ArgumentParser(description='3D Xanes Python Processing Tool')
	parser.add_argument('--filename', type=str, help='First file name to be processed',default='tiff')
	parser.add_argument('--method', type=str, help='Registration method',default='TranslationTransform')
	parser.add_argument('--config', type=str, help='Provide Config file',default='config.json')
	parser.add_argument('--log', type=str, help='Custom log file',default='x3py.log')
	
	
	args = parser.parse_args()

	#create outname
	tmp = args.filename.split('/')
	folder = '/'.join(tmp[:-1])
	tmp.insert(-1,'corrected')
 	
	ndir = '/'.join(tmp[:-1])
	make_dir(ndir)
	ext = args.filename.split('.')[-1]

	total = glob.glob(folder + "/*." + ext)
	total.sort()
	
	if int(len(total)) == 0:
		print('No files found.')
		sys.exit() 
	
	#Set reference and processing data list
	ref_name, total = total[0], total[1:]
	print("Using: ", ref_name, " as reference dataset\n")
	
	x3logging.logger.info("Processing now:\n")
	for i in total: x3logging.logger.info(i)
	
	#Define main function
	extra_args = [ref_name, args.method]
	
	#Initialize config and register
	pI = ProInit(ref_name)
	itkr = ITKregister(extra_args, pI.ReturnParameters())
	
	#Prepare file list
	CTdatasets = range(0,int(len(total)))
	return itkr, CTdatasets

#Prepare the job runner
def runreg(CTdatasets):
	itkr.ImgProcH5(CTdatasets)


if __name__ == "__main__":
	
	itkr, CTdatasets = main()
	#exit(0)
	#for i in CTdatasets:
	#	runreg(i)
	distribute_jobs(runreg, CTdatasets)
