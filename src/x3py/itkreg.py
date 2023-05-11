#Simple ITK based image registration
from utils import readh5, writeh5, readTIFF
import numpy as np
import SimpleITK as sitk
import glob
import x3logging
import sys


class ITKregister():
	#Initialize data registration methods
	def __init__(self,extra_args, par):
		x3logging.logger.info('Initialization ITKregister\n')
		#Reading dictionary
		self.par = par
		self.ref = extra_args[0]
		self.RMethod = extra_args[1]
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
		
		
	def command_iteration(self, method):
		print(
			f"{method.GetOptimizerIteration():3} "
			+ f"= {method.GetMetricValue():10.5f} "
			+ f": {method.GetOptimizerPosition()}"
		)	
		
	#Prepare for data processing
	def ImgProcH5(self, i):

		#Read the data		
		self.ar_fixed, ar_fxflat, ar_fxdark, self.theta = readh5(self.ref)
		self.fxflat = np.mean(ar_fxflat,axis=0)
		self.fxdark = np.mean(ar_fxdark,axis=0)
		
		ar_moving, ar_mvflat, ar_mvdark, theta = readh5(self.file_list[i])
		
		
		#Cast into 32bit
		self.ar_fixed = self.ar_fixed.astype('float32')
		ar_moving = ar_moving.astype('float32')
		
		#Create outname
		tmp = self.file_list[i].split('/')
		self.out_name = self.out_f + '/' + tmp[-1]
		x3logging.logger.info("File will be saved as: ")
		x3logging.logger.info(self.out_name)
		
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
		else:
			pass
		
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
				#print(type(self.ar_fixed),type(ar_moving))
				self.fixed_tmp = sitk.GetImageFromArray(self.ar_fixed[:,j,:])#,sitk.sitkFloat32)
				self.moving_tmp = sitk.GetImageFromArray(ar_moving[:,j,:])#,sitk.sitkFloat32)
				#print(type(self.moving_tmp),type(self.fixed_tmp))
				
				if self.RMethod == 'TranslationTransform':
					self.TranslationTransform()
				elif self.RMethod == 'BSplineTransformInitializer':
					self.BSplineTransformInitializer()
				else:
					x3logging.logger.critical('Unknown registration method. Check your config.json file')
	
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
				#print(type(self.ar_fixed),type(ar_moving))
				self.fixed_tmp = sitk.GetImageFromArray(self.ar_fixed[j,:,:])#,sitk.sitkFloat32)
				self.moving_tmp = sitk.GetImageFromArray(ar_moving[j,:,:])#,sitk.sitkFloat32)
				#print(type(self.moving_tmp),type(self.fixed_tmp))
				
				if self.RMethod == 'TranslationTransform':
					self.TranslationTransform()
				elif self.RMethod == 'BSplineTransformInitializer':
					self.BSplineTransformInitializer()
				else:
					x3logging.logger.critical('Unknown registration method. Check your config.json file')
	
				self.out = np.reshape(self.out, [sy,sx])
				self.buff[j,:,:] = self.out.astype('float32')
		else:
			x3logging.logger.critical('Unknown correction axis', self.par['CorrectionPlane'])
			sys.exit(0)
			
		
		#Save the data
		writeh5(self.out_name,self.buff, self.buffD, self.buffF, theta)
		x3logging.logger.info(self.out_name)
		x3logging.logger.info('written\n')
		
		
	def regTiffStack(self,i):	
		"""
			Register stack of TIFF images
		"""
		#Read the data		
		self.ar_fixedDATA, self.ar_fixedHEAD = readTIFF(self.ref)
		self.ar_movingDATA, self.ar_movingHEAD = readTIFF(self.file_list[i])	
	
		
		#Cast into 32bit
		self.ar_fixedDATA = self.ar_fixedDATA.astype('float32')
		self.ar_movingDATA = self.ar_movingDATA.astype('float32')
		
		#Create outname
		tmp = self.file_list[i].split('/')
		self.out_name = self.out_f + '/' + tmp[-1]
		x3logging.logger.info("File will be saved as: ")
		x3logging.logger.info(self.out_name)
		
		#apply crop		
		if (int(self.par['sy']) != int(self.par['ey']) or int(self.par['sx']) != int(self.par['ex'])):
			self.ar_movingDATA = self.ar_movingDATA[int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]
			self.ar_movingDATA = self.ar_movingDATA[int(self.par['sy']):int(self.par['ey']), \
											int(self.par['sx']):int(self.par['ex'])]			
		else:
			pass
		
		sy, sx = self.ar_movingDATA

		self.ar_fixedDATA = sitk.GetImageFromArray(self.ar_fixedDATA)#,sitk.sitkFloat32)
		self.ar_movingDATA = sitk.GetImageFromArray(self.ar_movingDATA)#,sitk.sitkFloat32)
		
		if self.RMethod == 'TranslationTransform':
			self.TranslationTransform()
		elif self.RMethod == 'BSplineTransformInitializer':
			self.BSplineTransformInitializer()
		else:
			x3logging.logger.critical('Unknown registration method. Check your config.json file')

		self.out = np.reshape(self.out, [sy,sx])
		self.buff[i,:,:] = self.out.astype('float32')

	def TranslationTransform(self):
		
		#Assuming similar orientation
		#initial_transform = sitk.CenteredTransformInitializer(self.fixed_tmp,self.moving_tmp,
		#												sitk.Euler2DTransform(), 
		#												sitk.CenteredTransformInitializerFilter.GEOMETRY)
		
		R = sitk.ImageRegistrationMethod()
		R.SetMetricAsMeanSquares()
		R.SetMetricSamplingStrategy(R.RANDOM)
		R.SetMetricSamplingPercentage(self.par['SetMetricSamplingPercentage'])
		R.SetOptimizerAsRegularStepGradientDescent(self.par['maxStep'], self.par['minStep'], self.par['numberOfIterations'])
		R.SetInitialTransform(sitk.TranslationTransform(self.fixed_tmp.GetDimension()))#initial_transform)#
		R.SetInterpolator(sitk.sitkLinear)

		R.AddCommand(sitk.sitkIterationEvent, lambda: self.command_iteration(R))

		outTx = R.Execute(self.fixed_tmp, self.moving_tmp)

		#Put it out in a logger
		x3logging.logger.info("-------")
		x3logging.logger.info(outTx)
		x3logging.logger.info(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
		x3logging.logger.info(f" Iteration: {R.GetOptimizerIteration()}")
		x3logging.logger.info(f" Metric value: {R.GetMetricValue()}")

		resampler = sitk.ResampleImageFilter()
		resampler.SetReferenceImage(self.fixed_tmp)
		resampler.SetInterpolator(sitk.sitkLinear)
		resampler.SetDefaultPixelValue(self.par['SetDefaultPixelValue'])
		resampler.SetTransform(outTx)
		#print(self.moving_tmp_nocrop.shape)
		#self.moving_tmp_nocrop = sitk.GetImageFromArray(self.moving_tmp)
		self.out = resampler.Execute(self.moving_tmp)
		
	def	BSplineTransformInitializer(self):
		def command_iterationB(method):
			print(
				f"{method.GetOptimizerIteration():3} "
				+ f"= {method.GetMetricValue():10.5f}"
			)
		transformDomainMeshSize = [8] * self.moving_tmp.GetDimension()
		tx = sitk.BSplineTransformInitializer(self.fixed_tmp, transformDomainMeshSize)

		x3logging.logger.info("Initial Parameters:")
		x3logging.logger.info(tx.GetParameters())

		R = sitk.ImageRegistrationMethod()
		R.SetMetricAsCorrelation()
		R.SetMetricSamplingStrategy(self.par['SamplingStrategy'])
		R.SetMetricSamplingPercentage(self.par['SetMetricSamplingPercentage'])

		R.SetOptimizerAsLBFGSB(
			gradientConvergenceTolerance=self.par['gradientConvergenceTolerance'],
			numberOfIterations=self.par['numberOfIterations'],
			maximumNumberOfCorrections=self.par['maximumNumberOfCorrections'],
			maximumNumberOfFunctionEvaluations=self.par['maximumNumberOfFunctionEvaluations'],
			costFunctionConvergenceFactor=self.par['costFunctionConvergenceFactor'],
			)
		R.SetInitialTransform(tx, True)
		R.SetInterpolator(sitk.sitkLinear)

		R.AddCommand(sitk.sitkIterationEvent, lambda: command_iterationB(R))

		outTx = R.Execute(self.fixed_tmp, self.moving_tmp)

		x3logging.logger.info("-------")
		x3logging.logger.info(outTx)
		x3logging.logger.info(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
		x3logging.logger.info(f" Iteration: {R.GetOptimizerIteration()}")
		x3logging.logger.info(f" Metric value: {R.GetMetricValue()}")

		#sitk.WriteTransform(outTx, args[3])

		resampler = sitk.ResampleImageFilter()
		resampler.SetReferenceImage(self.fixed_tmp)
		resampler.SetInterpolator(sitk.sitkLinear)
		resampler.SetDefaultPixelValue(self.par['SetDefaultPixelValue'])
		resampler.SetTransform(outTx)
		self.out = resampler.Execute(self.moving_tmp)
