#Simple ITK based image registration
from utils import readh5, writeh5
import numpy as np
import SimpleITK as sitk
import h5py


def command_iteration(method):
	print(
		f"{method.GetOptimizerIteration():3} "
		+ f"= {method.GetMetricValue():10.5f} "
		+ f": {method.GetOptimizerPosition()}"
	)

class ITKregister:

	#Initialize data registration methods
	def __init__(self,reference,args):
		print('Initialization\n')
		self.ar_fixed, ar_fxflat, ar_fxdark, self.theta = readh5(reference)
		self.fxflat = np.mean(ar_fxflat,axis=0)
		self.fxdark = np.mean(ar_fxdark,axis=0)
	
	#Prepare for data processing
	def ImgProc(self, file_name, out_name):
		#Read the data		
		ar_moving, ar_mvflat, ar_mvdark, theta = readh5(file_name)
		sz, sy, sx = ar_moving.shape

		#compute the average
		mvflat = np.mean(ar_mvflat,axis=0)
		mvdark = np.mean(ar_mvdark,axis=0)
		#Convert	    
		self.buff = np.zeros([sz,sy,sx],dtype='float32')
	    	
	    	#Perform the data registration
		for k in range(0,sz):
			#Flat field normalization
			self.fixed_tmp = (self.ar_fixed[k,:,:] - self.fxdark) / (self.fxflat - self.fxdark + 1e-3)
			self.moving_tmp = (ar_moving[k,:,:] - mvdark) / (mvflat - mvdark + 1e-3)
			#Data conversion
			self.fixed_tmp = sitk.GetImageFromArray(self.fixed_tmp)#,sitk.sitkFloat32)
			self.moving_tmp = sitk.GetImageFromArray(self.moving_tmp)#,sitk.sitkFloat32)

			self.ImgReg()

			self.out = np.reshape(self.out, [sy,sx])
			self.buff[k,:,:] = self.out.astype('float32')
		
		#Save the data
		writeh5(out_name,self.buff, mvdark/mvdark, mvflat/mvflat, theta)
		print(out_name,' written\n')
			
	#USE Simple ITK for data registration
	def ImgReg(self):
		R = sitk.ImageRegistrationMethod()
		R.SetMetricAsMeanSquares()
		R.SetOptimizerAsRegularStepGradientDescent(4.0, 0.01, 200)
		R.SetInitialTransform(sitk.TranslationTransform(self.fixed_tmp.GetDimension()))
		R.SetInterpolator(sitk.sitkLinear)

		R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))

		outTx = R.Execute(self.fixed_tmp, self.moving_tmp)

		print("-------")
		print(outTx)
		print(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
		print(f" Iteration: {R.GetOptimizerIteration()}")
		print(f" Metric value: {R.GetMetricValue()}")

		resampler = sitk.ResampleImageFilter()
		resampler.SetReferenceImage(self.fixed_tmp)
		resampler.SetInterpolator(sitk.sitkLinear)
		resampler.SetDefaultPixelValue(1.0)
		resampler.SetTransform(outTx)

		self.out = resampler.Execute(self.moving_tmp)
