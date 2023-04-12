#Simple ITK based image registration
from utils import readh5, writeh5, make_dir
import numpy as np
import SimpleITK as sitk
import h5py
import glob

def command_iteration(self, method):
	print(
		f"{method.GetOptimizerIteration():3} "
		+ f"= {method.GetMetricValue():10.5f} "
		+ f": {method.GetOptimizerPosition()}"
	)


class ITKregister():
	#Initialize data registration methods
	def __init__(self,ref_name):
		print('Initialization\n')
		self.ref = ref_name
		#create outname
		tmp = self.ref.split('/')
		folder = '/'.join(tmp[:-1])
		tmp.insert(-1,'corrected')
	 	
		self.out_name = '/'.join(tmp)
		ext = self.ref.split('.')[-1]

		total = glob.glob(folder + "/*." + ext)

		total.sort()
		self.file_list = total
		
	#Prepare for data processing
	def ImgProc(self, i):

		#Read the data		
		self.ar_fixed, ar_fxflat, ar_fxdark, self.theta = readh5(self.ref)
		self.fxflat = np.mean(ar_fxflat,axis=0)
		self.fxdark = np.mean(ar_fxdark,axis=0)
		
		ar_moving, ar_mvflat, ar_mvdark, theta = readh5(self.file_list[i])
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
			self.fixed_tmp = (self.ar_fixed[k,:,:] - self.fxdark) / (self.fxflat - self.fxdark + 1e-3)
			self.moving_tmp = (ar_moving[k,:,:] - mvdark) / (mvflat - mvdark + 1e-3)
			#Data conversion
			self.fixed_tmp = sitk.GetImageFromArray(self.fixed_tmp)#,sitk.sitkFloat32)
			self.moving_tmp = sitk.GetImageFromArray(self.moving_tmp)#,sitk.sitkFloat32)

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

			self.out = np.reshape(self.out, [sy,sx])
			self.buff[k,:,:] = self.out.astype('float32')
		
		#Save the data
		writeh5(out_name,self.buff, self.buffD, self.buffF, theta)
		print(out_name,' written\n')
