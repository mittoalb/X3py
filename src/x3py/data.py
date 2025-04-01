#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# *************************************************************************** #
#                  Copyright © 2023, UChicago Argonne, LLC                    #
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
x3py data structure & Reader


Created on Wed May 10 15:39:13 2023

@author: amittone

"""
import numpy as np
import h5py
import tifffile as tiff
import glob
from x3py import x3logging
import os
import sys
import fabio

x3l = x3logging.getLogger(__name__)
x3l.setLevel(x3logging.DEBUG)

def readh5(file_name):
	"""
		Read HDF5 file, return numpy arrays
	"""
	fx = h5py.File(file_name,'r')
	fixed, fxflat, fxdark, theta, energy = fx['/exchange/data'], \
										fx['/exchange/data_white'], \
										fx['/exchange/data_dark'], \
										fx['/exchange/theta'], \
										fx['/measurment/instrument/monochromator/energy']
	return np.asarray(fixed), np.asarray(fxflat), np.asarray(fxdark), theta, energy


def writeh5APS(file_name,buff, darks, flats, theta, energy):
	"""
		Write a HDF5 file. Minimal data structure compatible with tomography reconstructions.
	"""
	with h5py.File(file_name,'w') as f:
		a = f.create_group('exchange')
		a.create_dataset('data',data=buff,dtype='float32')
		a.create_dataset('data_dark',data=darks,dtype='float32')
		a.create_dataset('data_white',data=flats,dtype='float32')
		a.create_dataset('theta',data=theta)
		a.create_dataset('energy',data=energy)

def writeh5REG(file_name,buff, energy, *args):
	"""
		Write a HDF5 file. Minimal data structure compatible with tomography reconstructions.
	"""
	with h5py.File(file_name,'w') as f:
		a = f.create_group('exchange')
		a.create_dataset('data',data=buff,dtype='float32')
		b = f.create_group('processing')
		c = b.create_group('registration')
		b.create_dataset('energy',data=energy,dtype='float32')
		if len(args) != 0:
			R = args[0]
			b.create_dataset('IsRef',data=False)
			c.create_dataset('OptimizerStopConditionDescription', \
					data=R.GetOptimizerStopConditionDescription())#,dtype='float32')
			c.create_dataset('Iteration',data=R.GetOptimizerIteration())#,dtype='float32')
		else:
			b.create_dataset('IsRef',data=True)

def readTIFVOL(path):
	"""
	Parameters
	----------
	path : TYPE
		DESCRIPTION.

	Returns
	-------
	TYPE
		DESCRIPTION.

	"""
	FileList = glob.glob(path + "/*.tiff")
	FileList.sort()
	
	if not len(FileList):
		try:
			x3l.error("No data found!")
		except NameError:
			print("No data found")
		sys.exit(0)

	datavol = []
	for e in FileList:
		with tiff.TiffFile(e) as tif:
			datavol.append(tif.pages[0].asarray())
	return np.array(datavol)

def saveTIFVOL(datavol, path, filename):
	"""
	Parameters
	----------
	datavol : TYPE
		DESCRIPTION.
	path : TYPE
		DESCRIPTION.
	filename : TYPE
		DESCRIPTION.

	Returns
	-------
	None.

	"""
	for i, image in enumerate(datavol):
		filename = path + filename + f"_{i}.tiff"
		tiff.imwrite(filename, image)
		try:
			x3l.info(filename, "written on disk")
		except NameError:
			pass
		
def getFolderList(prefix,epoints):
	"""
	folder_list[0]: Reference dataset.
	folder_list[1:]: Datasets to be registered
	"""
	folder_list = glob.glob(prefix + "*")
	folder_list.sort()

	#To avoid errors in case of files
	for el in folder_list:
		if os.path.isdir(el):
			pass
		else:
			folder_list.remove(el)
	if not len(folder_list):
		try:
			x3l.error("No data found!")
		except NameError:
			print("No data found")
		sys.exit(0)
	else:
		return folder_list[0], folder_list[1:]
	
	
	def readTIFF(file_name):
		return fabio.open(file_name)

	def writeTIFF(file_name,data):
		data.write(file_name)
		