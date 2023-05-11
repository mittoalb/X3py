#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 13 11:51:30 2023

@author: amittone
"""
import os.path
import json
import x3logging

class ProInit():
	def __init__(self,ref_name):
		#Config initialization
		x3logging.logger.info('Initialization ProInit\n')
		path = 'config.json'
		self.ref_name = ref_name
		if os.path.isfile(path):
			x3logging.logger.info('Reading config.json\n')
			try:
				with open(path, 'r') as j:
					self.par = json.loads(j.read())
			except json.JSONDecodeError:
				x3logging.logger.warning('Corrupted config.json. Creating a new one\n')
				self.config_init()
		else:
			x3logging.logger.info('Creating config.json\n')
			self.config_init()
	
	def config_init(self):
		self.par = {}
		try:
			import datetime
			self.par['Create on'] = str(datetime.date.today())
		except ImportError:
			x3logging.logger.info('Cannot add a date in the config file. ')
			pass
		#Plane of correction
		self.par['CorrectionPlane'] = 'XY'
		#TranslationTransform method
		self.par['ref_name'] = self.ref_name
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
		
		
		#Flat field correction regularization
		self.par['FDreg'] = 1e-3
		
		with open("config.json", "w") as fp:
			json.dump(self.par, fp)
		x3logging.logger.info("config.json written.")
		
	def ReturnParameters(self):
		return self.par