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

@author: amittone
"""
import os.path
import json
from x3py import x3logging


x3l = x3logging.getLogger(__name__)
x3l.setLevel(x3logging.DEBUG)

class ProInit():
	def __init__(self,Json_name):
		#Config initialization
		x3l.info('Initialization ProInit\n')
		self.Json_name = Json_name
		#self.ref_name = ref_name
		if os.path.isfile(Json_name):
			x3l.info('Reading config.json\n')
			try:
				with open(self.Json_name, 'r') as j:
					self.par = json.loads(j.read())
			except json.JSONDecodeError:
				x3l.warning('Corrupted config.json. Creating a new one\n')
				self.config_init()
		else:
			x3l.info('Creating config.json\n')
			self.config_init()
	
	def config_init(self):
		self.par = {}
		try:
			import datetime
			self.par['Created: '] = str(datetime.date.today())
		except ImportError:
			x3l.info('Cannot add a date in the config file. ')
			pass
		#Plane of correction
		self.par['CorrectionPlane'] = 'XY'
		#TranslationTransform method
		self.par['ref_name'] = "RefName"#self.ref_name
		self.par['maxStep'] = 4.0
		self.par['minStep'] = 0.01
		self.par['numberOfIterations'] = 200
		self.par['relaxationFactor'] = 0.5
		self.par['SetDefaultPixelValue'] = 1.0
		
		#BSplineTransformInitializer method
		self.par['gradientConvergenceTolerance']=1e-5
		self.par['numberOfIterations']=100
		self.par['maximumNumberOfCorrections']=5
		self.par['maximumNumberOfFunctionEvaluations']=1000
		self.par['costFunctionConvergenceFactor']=1e7
		self.par['transformDomainMeshSize'] = 8
		
		#ROI Definition
		self.par['sx']=0
		self.par['ex']=0
		self.par['sy']=0
		self.par['ey']=0
		
		#Methods
		self.par['SamplingStrategy'] = "R.RANDOM"
		self.par['SetMetricSamplingPercentage'] = 0.01
		
		#CTDATA parameters
		self.par['CROP'] = False
		self.par['sx']=0
		self.par['ex']=0
		self.par['sy']=0
		self.par['ey']=0
		self.par['sz']=0
		self.par['ez']=0
		
		self.par['epoints']=20
		self.par['Start_energy']=8.45
		self.par['EndEnergy']=8.55

		self.par['DataPrefix']="/prefix/of/reconstructed/folders"
		
		
		self.par['learningRate']=1.0
		self.par['numberOfIterations']=200
		self.par['convergenceMinimumValue']=1e-5
		self.par['convergenceWindowSize']=5
		

		
		#Flat field correction regularization
		self.par['FDreg'] = 1e-3
		
		with open("./" + self.Json_name, "w") as fp:
			json.dump(self.par, fp)
		x3l.info("config.json written.")
		
	def ReturnParameters(self):
		return self.par
	
	def updateParameters(self,par):
		with open("./" + self.Json_name, "w") as fp:
			json.dump(par, fp)
		x3l.info(self.Json_name, "written")