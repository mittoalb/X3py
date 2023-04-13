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
					self.par_dic = json.loads(j.read())
			except json.JSONDecodeError:
				x3logging.logger.warning('Corrupted config.json. Creating a new one\n')
				self.config_init()
		else:
			x3logging.logger.info('Creating config.json\n')
			self.config_init()
	
	def config_init(self):
		self.par_dic = {}
		try:
			import datetime
			self.par_dic['Create on'] = str(datetime.date.today())
		except ImportError:
			x3logging.logger.info('Cannot add a date in the config file. ')
			pass
		#TranslationTransform method
		self.par_dic['ref_name'] = self.ref_name
		self.par_dic['maxStep'] = 4.0
		self.par_dic['minStep'] = 0.01
		self.par_dic['numberOfIterations'] = 200
		self.par_dic['relaxationFactor'] = 0.5
		self.par_dic['SetDefaultPixelValue'] = 1.0
		
		#BSplineTransformInitializer method
		self.par_dic['gradientConvergenceTolerance']=1e-5
		self.par_dic['numberOfIterations']=100
		self.par_dic['maximumNumberOfCorrections']=5
		self.par_dic['maximumNumberOfFunctionEvaluations']=1000
		self.par_dic['costFunctionConvergenceFactor']=1e7
		self.par_dic['transformDomainMeshSize'] = 8
		
		#Flat field correction regularization
		self.par_dic['FDreg'] = 1e-3
		
		with open("config.json", "w") as fp:
			json.dump(self.par_dic, fp)
		x3logging.logger.info("config.json written.")
		
	def ReturnParameters(self):
		return self.par_dic