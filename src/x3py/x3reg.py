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
Created on Thu Apr 13 11:51:30 2023
Simple ITK based image registration

@author: amittone
"""

from x3py.utils import distribute_jobs
from x3py.data import readh5, readTIFVOL, saveTIFVOL, getFolderList, writeh5REG, writeh5APS
import numpy as np
import SimpleITK as sitk
import glob
from x3py import x3logging
import sys

x3l = x3logging.getLogger(__name__)
x3l.setLevel(x3logging.DEBUG)


class ITKregistration():
	#Initialize data registration methods
	def __init__(self,extra_args, par):
		x3l.info('Initialization ITKregister\n')
		#Reading dictionary
		self.par = par
		self.ref = extra_args[0]
		self.RMethod = extra_args[1]

	#Read custom ITK registration with required input parameters
	def ReadCustomITKReg(self,func,func_par):#ITKCustom_params):
		self.func = func
		#merge two dictionaries
		self.par.update(func_par)
		
		
	def returnDic(self):
		"""
		Debug utility
		"""
		return self.par
		
	#Prepare for data processing
	def ProjREG(self, i):
		#create outname
		tmp = self.ref.split('/')
		folder = '/'.join(tmp[:-1])
		tmp.insert(-1,'corrected')
		tmp = tmp[:-1]
	 	
		self.out_f = '/'.join(tmp)
		ext = self.ref.split('.')[-1]

		total = glob.glob(folder + "/*." + ext)
		total.sort()
		self.file_list = total
		self.NoFiles = int(len(total))		
		
		#Read the data		
		self.ar_fixed, ar_fxflat, ar_fxdark, self.theta, self.energyR = readh5(self.ref)
		self.fxflat = np.mean(ar_fxflat,axis=0)
		self.fxdark = np.mean(ar_fxdark,axis=0)
		
		ar_moving, ar_mvflat, ar_mvdark, theta, energyM = readh5(self.file_list[i])
		
		
		#Cast into 32bit
		self.ar_fixed = self.ar_fixed.astype('float32')
		ar_moving = ar_moving.astype('float32')
		
		#Create outname
		tmp = self.file_list[i].split('/')
		self.out_name = self.out_f + '/' + tmp[-1]
		x3l.info("File will be saved as: ")
		x3l.info(self.out_name)
		
		#apply crop		
		if (int(self.par['sy']) != int(self.par['ey']) or int(self.par['sx']) != int(self.par['ex'])):
			ar_moving = ar_moving[:,int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]
			self.ar_fixed = self.ar_fixed[:,int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]
			ar_mvflat = ar_mvflat[:,int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]
			ar_mvdark = ar_mvdark[:,int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]	
			self.fxflat = self.fxflat[int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]	
			self.fxdark = self.fxdark[int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]

		sz, sy, sx = ar_moving.shape
		szf, syf, sxf = ar_mvflat.shape
		szd, syd, sxd = ar_mvdark.shape
		#compute the average
		mvflat = np.mean(ar_mvflat,axis=0)
		mvdark = np.mean(ar_mvdark,axis=0)
		#Convert	    
		self.buff = np.zeros([sz,sy,sx],dtype='float32')
		self.buffF = np.ones([szf,syf,sxf],dtype='float32')
		self.buffD = np.zeros([szd,syd,sxd],dtype='float32')
	    	
		if self.par['CorrectionPlane'] == 'XZ':	
			#Perform the data registration
			for k in range(0,sz):
				#Flat field normalization
				self.ar_fixed[k,:,:] = (self.ar_fixed[k,:,:] - self.fxdark) / \
									(self.fxflat - self.fxdark + self.par['FDreg'])
				ar_moving[k,:,:] = (ar_moving[k,:,:] - mvdark) / \
									(mvflat - mvdark + self.par['FDreg'])
				
			for j in range(0,sy):
				#Data conversion
				self.fixed_tmp = sitk.GetImageFromArray(self.ar_fixed[:,j,:])#,sitk.sitkFloat32)
				self.moving_tmp = sitk.GetImageFromArray(ar_moving[:,j,:])#,sitk.sitkFloat32)
				
				if self.RMethod == 'ITKCustom':
					out, R = self.func(self.fixed_tmp,self.moving_tmp,self.par)	
				else:
					x3l.critical('Unknown registration method. Check your config.json file')
	
				self.out = np.reshape(self.out, [sz,sx])
				self.buff[:,j,:] = self.out.astype('float32')
		elif self.par['CorrectionPlane'] == 'XY':
	    	#Perform the data registration
			for j in range(0,sz):
				self.ar_fixed[j,:,:] = (self.ar_fixed[j,:,:] - self.fxdark) / \
									(self.fxflat - self.fxdark + self.par['FDreg'])
				ar_moving[j,:,:] = (ar_moving[j,:,:] - mvdark) / \
									(mvflat - mvdark + self.par['FDreg'])
				#Data conversion
				self.fixed_tmp = sitk.GetImageFromArray(self.ar_fixed[j,:,:])#,sitk.sitkFloat32)
				self.moving_tmp = sitk.GetImageFromArray(ar_moving[j,:,:])#,sitk.sitkFloat32)

				if self.RMethod == 'ITKCustom':
					out, R = self.func(self.fixed_tmp,self.moving_tmp,self.par)	
				else:
					x3l.critical('Unknown registration method. Check your config.json file')
	
				self.out = np.reshape(self.out, [sy,sx])
				self.buff[j,:,:] = self.out.astype('float32')
		else:
			x3l.critical('Unknown correction axis', self.par['CorrectionPlane'])
			sys.exit(0)
		#Save the data
		writeh5APS(self.out_name,self.buff, self.buffD, self.buffF, theta, energyM)
		x3l.info(self.out_name)
		x3l.info('written\n')
		
		
	def CTREG(self):
		"""
		Returns
		-------
		None.

		"""
		#Read data path
		print(self.par)
		ref_path, self.mov_paths = getFolderList(self.par['DataPrefix'],self.par['epoints'])

		#Read reference
		self.ref_data = readTIFVOL(ref_path)
		x3l.info(ref_path)

		#CROP DATA
		if self.par['CROP']:
			self.ref_data = self.ref_data[int(self.par['sz']):int(self.par['ez']), \
						  int(self.par['sy']):int(self.par['ey']), \
						  int(self.par['sx']):int(self.par['ex'])]

		self.ar_fxd = sitk.GetImageFromArray(self.ref_data)
		#Save reference crop
		file_name = ref_path + "Reg.h5"
		writeh5REG(file_name,self.ref_data,0)

		#Create range for multiprocessing
		datapoints = range(0,self.par['epoints']-1)
		self.enpoints = np.linspace(float(self.par['Start_energy']),float(self.par['EndEnergy']),int(self.par['epoints']))
		distribute_jobs(self.run_regCT,datapoints)
		

	def run_regCT(self,i):
		mov_data = readTIFVOL(self.mov_paths[i])
		#Crop the data & convert into sitk dataformat   
		if self.par['CROP']:
			mov_data = mov_data[int(self.par['sz']):int(self.par['ez']), \
						  int(self.par['sy']):int(self.par['ey']), \
						  int(self.par['sx']):int(self.par['ex'])]
		ar_mov = sitk.GetImageFromArray(mov_data)
		
		if self.RMethod == 'ITKCustom':
			out, R = self.func(self.ar_fxd,ar_mov,self.par)
		else:
			x3l.critical('Unknown registration method. Check your config.json file')
			
		out = np.reshape(out, [int(self.par['ez'])-int(self.par['sz']), \
								int(self.par['ey'])-int(self.par['sy']), \
								int(self.par['ex'])-int(self.par['sx'])])
		out = out.astype('float32')
		file_name = self.mov_paths[i] + "Reg.h5"
		writeh5REG(file_name,out, self.enpoints[i],R)
		x3l.info(file_name, "saved")