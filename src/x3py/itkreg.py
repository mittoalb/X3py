#Simple ITK based image registration
from utils import readh5, writeh5
import numpy as np
import SimpleITK as sitk
import glob
import x3logging


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
		
		
	def command_iteration(self, method):
		print(
			f"{method.GetOptimizerIteration():3} "
			+ f"= {method.GetMetricValue():10.5f} "
			+ f": {method.GetOptimizerPosition()}"
		)	
		
	#Prepare for data processing
	def ImgProc(self, i):

		#Read the data		
		self.ar_fixed, ar_fxflat, ar_fxdark, self.theta = readh5(self.ref)
		self.fxflat = np.mean(ar_fxflat,axis=0)
		self.fxdark = np.mean(ar_fxdark,axis=0)
		
		ar_moving, ar_mvflat, ar_mvdark, theta = readh5(self.file_list[i])
		
		#Create outname
		tmp = self.file_list[i].split('/')
		self.out_name = self.out_f + '/' + tmp[-1]
		x3logging.logger.info("File will be saved as: ")
		x3logging.logger.info(self.out_name)

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
	    	
	    	
	    	#Perform the data registration
		for k in range(0,sz):
			#Flat field normalization
			self.fixed_tmp = (self.ar_fixed[k,:,:] - self.fxdark) / (self.fxflat - self.fxdark + self.par['FDreg'])
			self.moving_tmp = (ar_moving[k,:,:] - mvdark) / (mvflat - mvdark + self.par['FDreg'])
			#Data conversion
			self.fixed_tmp = sitk.GetImageFromArray(self.fixed_tmp)#,sitk.sitkFloat32)
			self.moving_tmp = sitk.GetImageFromArray(self.moving_tmp)#,sitk.sitkFloat32)

			if self.RMethod == 'TranslationTransform':
				self.TranslationTransform()
			elif self.RMethod == 'BSplineTransformInitializer':
				self.BSplineTransformInitializer()
			else:
				x3logging.logger.critical('Unknown registration method. Check your config.json file')

			self.out = np.reshape(self.out, [sy,sx])
			self.buff[k,:,:] = self.out.astype('float32')
		
		#Save the data
		writeh5(self.out_name,self.buff, self.buffD, self.buffF, theta)
		x3logging.logger.info(self.out_name)
		x3logging.logger.info('written\n')

	def TranslationTransform(self):
		
		R = sitk.ImageRegistrationMethod()
		R.SetMetricAsMeanSquares()
		R.SetOptimizerAsRegularStepGradientDescent(self.par['maxStep'], self.par['minStep'], self.par['numberOfIterations'])
		R.SetInitialTransform(sitk.TranslationTransform(self.fixed_tmp.GetDimension()))
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
