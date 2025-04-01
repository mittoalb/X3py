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
"""
Created on Thu May 11 15:31:55 2023

@author: amittone


Reference:
	
	https://simpleitk.readthedocs.io/en/master/
"""
import SimpleITK as sitk
from x3py import x3logging
import sys

x3l = x3logging.getLogger(__name__)
x3l.setLevel(x3logging.DEBUG)

def TranslationTransform(fx_ar,mv_ar, par):
	"""
	Parameters
	----------
	par : parameters dictionary
		par['SetMetricSamplingPercentage'] = 0.01
		par['maxStep'] = 4
		par['minStep'] = 0.01
		par['numberOfIterations'] = 200
		par['SetDefaultPixelValue'] = 1
		
	fx_ar : reference volume
		sitk array.
	mv_ar : volume to be aligned
		sitk array.

	Returns
	-------
	TYPE
		registered volume.
		numpy array

	Reference:
	SimpleITK
	https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationMethod1_docs.html
	"""
	
	#Assuming similar orientation
	#initial_transform = sitk.CenteredTransformInitializer(self.fixed_tmp,self.moving_tmp,
	#												sitk.Euler2DTransform(), 
	#												sitk.CenteredTransformInitializerFilter.GEOMETRY)
	def command_iteration(method):
		print(
			f"{method.GetOptimizerIteration():3} "
			+ f"= {method.GetMetricValue():10.5f} "
			+ f": {method.GetOptimizerPosition()}"
		)
	R = sitk.ImageRegistrationMethod()
	R.SetMetricAsMeanSquares()
	R.SetMetricSamplingStrategy(R.RANDOM)
	R.SetMetricSamplingPercentage(float(par['SetMetricSamplingPercentage']))
	R.SetOptimizerAsRegularStepGradientDescent(float(par['maxStep']), float(par['minStep']), int(par['numberOfIterations']))
	R.SetInitialTransform(sitk.TranslationTransform(fx_ar.GetDimension()))#initial_transform)#
	R.SetInterpolator(sitk.sitkLinear)

	R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))

	outTx = R.Execute(fx_ar, mv_ar)

	#Put it out in a logger
	x3l.info("-------")
	x3l.info(outTx)
	x3l.info(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
	x3l.info(f" Iteration: {R.GetOptimizerIteration()}")
	x3l.info(f" Metric value: {R.GetMetricValue()}")

	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fx_ar)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(int(par['SetDefaultPixelValue']))
	resampler.SetTransform(outTx)
	#print(self.moving_tmp_nocrop.shape)
	#self.moving_tmp_nocrop = sitk.GetImageFromArray(self.moving_tmp)
	return resampler.Execute(mv_ar), R
	
def	BSplineTransformInitializer1(fx_ar,mv_ar, par):
	"""
	Parameters
	----------
	par : parameters dictionary
		DESCRIPTION.
	fx_ar : reference volume
		sitk array.
	mv_ar : volume to be aligned
		sitk array.
		
	Dictinoary:
		
	par['gradientConvergenceTolerance'] = 1e-5
	par['numberOfIterations']= 100
	par['maximumNumberOfCorrections']= 5
	par['maximumNumberOfFunctionEvaluations']= 1000
	par['costFunctionConvergenceFactor']= 1e7
	par['SetDefaultPixelValue'] = 1

	Returns
	-------
	TYPE
		registered volume.
		numpy array

	Reference:
	SimpleITK
	https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationMethodBSpline1_docs.html
	"""
	def command_iteration(method):
		print(
			f"{method.GetOptimizerIteration():3} "
			+ f"= {method.GetMetricValue():10.5f}"
		)
	transformDomainMeshSize = [8] * mv_ar.GetDimension()
	tx = sitk.BSplineTransformInitializer(fx_ar, transformDomainMeshSize)

	x3l.info("Initial Parameters:")
	x3l.info(tx.GetParameters())

	R = sitk.ImageRegistrationMethod()
	R.SetMetricAsCorrelation()
	R.SetMetricSamplingStrategy(par['SamplingStrategy'])
	R.SetMetricSamplingPercentage(par['SetMetricSamplingPercentage'])

	R.SetOptimizerAsLBFGSB(
		gradientConvergenceTolerance=float(par['gradientConvergenceTolerance']),
		numberOfIterations=int(par['numberOfIterations']),
		maximumNumberOfCorrections=int(par['maximumNumberOfCorrections']),
		maximumNumberOfFunctionEvaluations=int(par['maximumNumberOfFunctionEvaluations']),
		costFunctionConvergenceFactor=float(par['costFunctionConvergenceFactor']),
		)
	R.SetInitialTransform(tx, True)
	R.SetInterpolator(sitk.sitkLinear)

	R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))

	outTx = R.Execute(fx_ar, mv_ar)

	x3l.info("-------")
	x3l.info(outTx)
	x3l.info(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
	x3l.info(f" Iteration: {R.GetOptimizerIteration()}")
	x3l.info(f" Metric value: {R.GetMetricValue()}")

	#sitk.WriteTransform(outTx, args[3])

	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fx_ar)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(float(par['SetDefaultPixelValue']))
	resampler.SetTransform(outTx)
	return resampler.Execute(mv_ar), R

def TranslationTransformJHM(fx_ar,mv_ar,par):
	"""
	Parameters
	----------
	fx_ar : reference volume
		sitk array.
	mv_ar : volume to be aligned
		sitk array.
		
	Dictionary:
		
	par['learningRate'] = 1.0
	par['numberOfIterations'] = 200
	par['convergenceMinimumValue'] = 1e-5
	par['convergenceWindowSize'] = 5

	Returns
	-------
	TYPE
		registered volume.
		numpy array
		
	Reference:
	SIMPLEITK
	https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationMethod2_docs.html
	"""
	
	def command_iteration(method):
		print(
			f"{method.GetOptimizerIteration():3} "
			+ f" = {method.GetMetricValue():7.5f} "
			+ f" : {method.GetOptimizerPosition()}"
		)

	R = sitk.ImageRegistrationMethod()

	R.SetMetricAsJointHistogramMutualInformation()

	R.SetOptimizerAsGradientDescentLineSearch(
		learningRate=float(par['learningRate']),
		numberOfIterations=int(par['numberOfIterations']),
		convergenceMinimumValue=float(par['convergenceMinimumValue']),
		convergenceWindowSize=int(par['convergenceWindowSize']),
	)

	R.SetInitialTransform(sitk.TranslationTransform(fx_ar.GetDimension()))

	R.SetInterpolator(sitk.sitkLinear)

	R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))

	outTx = R.Execute(fx_ar, mv_ar)

	x3l.info("-------")
	x3l.info(outTx)
	x3l.info(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
	x3l.info(f" Iteration: {R.GetOptimizerIteration()}")
	x3l.info(f" Metric value: {R.GetMetricValue()}")

	#sitk.WriteTransform(outTx, args[3])

	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fx_ar)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(1)
	resampler.SetTransform(outTx)

	return resampler.Execute(mv_ar), R


def Displacement1(fixed, moving, par):#TMJHM=20, lr=1.0, noi=100):
	"""
	Parameters
	----------
	fixed : ITK.array
		Input reference volume.
	moving : ITK.array
		Input volume to be aligned.
	
	Dictionary:
		part['TMJHM'] = 20 SetMetricAsJointHistogramMutualInformation
		par['learningRate'] = 1.0
		par['numberOfIterations'] = 300
		par['SetDefaultPixelValue'] = 1
		
	Returns
	-------
	numpy.array
		registered volume. It needs to be reshaped and transformed into float32
	R : object
		Transform details.
	"""

	def command_iteration(method):
		if method.GetOptimizerIteration() == 0:
			print(f"\tLevel: {method.GetCurrentLevel()}")
			print(f"\tScales: {method.GetOptimizerScales()}")
		print(f"#{method.GetOptimizerIteration()}")
		print(f"\tMetric Value: {method.GetMetricValue():10.5f}")
		print(f"\tLearningRate: {method.GetOptimizerLearningRate():10.5f}")
		if method.GetOptimizerConvergenceValue() != sys.float_info.max:
			print(
				"\tConvergence Value: "
				+ f"{method.GetOptimizerConvergenceValue():.5e}"
			)
	
	
	def command_multiresolution_iteration(method):
		print(f"\tStop Condition: {method.GetOptimizerStopConditionDescription()}")
		print("============= Resolution Change =============")
	
	initialTx = sitk.CenteredTransformInitializer(
		fixed, moving, sitk.AffineTransform(fixed.GetDimension())
	)
	
	R = sitk.ImageRegistrationMethod()
	
	R.SetShrinkFactorsPerLevel([3, 2, 1])
	R.SetSmoothingSigmasPerLevel([2, 1, 1])
	
	R.SetMetricAsJointHistogramMutualInformation(int(par['TMJHM']))
	R.MetricUseFixedImageGradientFilterOff()
	
	R.SetOptimizerAsGradientDescent(
		learningRate=float(par['learningRate']),
		numberOfIterations=int(par['numberOfIterations']),
		estimateLearningRate=R.EachIteration,
	)
	R.SetOptimizerScalesFromPhysicalShift()
	
	R.SetInitialTransform(initialTx)
	
	R.SetInterpolator(sitk.sitkLinear)
	
	R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))
	R.AddCommand(
		sitk.sitkMultiResolutionIterationEvent,
		lambda: command_multiresolution_iteration(R),
	)
	
	outTx1 = R.Execute(fixed, moving)
	
	print("-------")
	print(outTx1)
	print(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
	print(f" Iteration: {R.GetOptimizerIteration()}")
	print(f" Metric value: {R.GetMetricValue()}")
	
	displacementField = sitk.Image(fixed.GetSize(), sitk.sitkVectorFloat64)
	displacementField.CopyInformation(fixed)
	displacementTx = sitk.DisplacementFieldTransform(displacementField)
	del displacementField
	displacementTx.SetSmoothingGaussianOnUpdate(
	    varianceForUpdateField=0.0, varianceForTotalField=1.5
	)
	
	R.SetMovingInitialTransform(outTx1)
	R.SetInitialTransform(displacementTx, inPlace=True)
	
	R.SetMetricAsANTSNeighborhoodCorrelation(4)
	R.MetricUseFixedImageGradientFilterOff()
	
	R.SetShrinkFactorsPerLevel([3, 2, 1])
	R.SetSmoothingSigmasPerLevel([2, 1, 1])
	
	R.SetOptimizerScalesFromPhysicalShift()
	R.SetOptimizerAsGradientDescent(
		learningRate=float(par['learningRate']),
		numberOfIterations=int(par['numberOfIterations'])*3,
		estimateLearningRate=R.EachIteration,
	)
	
	R.Execute(fixed, moving)
	compositeTx = sitk.CompositeTransform([outTx1, displacementTx])
	
	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(int(par['SetDefaultPixelValue']))
	resampler.SetTransform(compositeTx)

	return resampler.Execute(moving), R



def OptimizerWeights(fixed, moving, par):
	"""
	3D rigid transformation using the Euler parameterization, but we only allow rotation around the z axis. 
	As there is no transformation that represents this subspace of rigid transformations, we use the SetOptimizerWeights method to disable rotations around the x and y axes. 
	The order of the weights in the weights parameter matches the order of parameters returned from the transformation GetParameters method. 
	For the Euler3DTransform the order is [angleX, angleY, angleZ, tx, ty, tz], so our weights vector is [0,0,1,1,1,1].
	Reference:
	https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationOptimizerWeights_docs.html

	Parameters
	----------
	fixed : ITK array
		Input reference volume.
	moving : ITK array
		Input volume to be aligned.
	par : Dictionary
		par['learningRate'] = 1.0
		par['numberOfIterations'] = 300
		par['convergenceMinimumValue'] = 1e-6
		par['convergenceWindowSize'] = 10

	Returns
	-------
	Registered volume. Arra yto be reshaped
	R: Registration info

	"""	
	# initialization
	transform = sitk.CenteredTransformInitializer(
		fixed,
		moving,
		sitk.Euler3DTransform(),
		sitk.CenteredTransformInitializerFilter.GEOMETRY,
	)
	# registration
	R = sitk.ImageRegistrationMethod()
	R.SetMetricAsCorrelation()
	R.SetMetricSamplingStrategy(R.NONE)
	R.SetInterpolator(sitk.sitkLinear)
	R.SetOptimizerAsGradientDescent(
		learningRate=par['learningRate'],
		numberOfIterations=par['numberOfIterations'],
		convergenceMinimumValue=par['convergenceMinimumValue'],
		convergenceWindowSize=par['convergenceWindowSize'],
	)
	R.SetOptimizerScalesFromPhysicalShift()
	R.SetInitialTransform(transform, inPlace=True)
	R.SetOptimizerWeights([0, 0, 1, 1, 1, 1])
	outTx = R.Execute(fixed, moving)
	
	print("-------")
	print(f"Final transform parameters: {transform.GetParameters()}")
	print(
	   "Optimizer stop condition: "
         + f"{R.GetOptimizerStopConditionDescription()}"
	)
	print(f"Iteration: {R.GetOptimizerIteration()}")
	print(f"Metric value: {R.GetMetricValue()}")
	
	sitk.WriteTransform(transform, sys.argv[3])
	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(1)
	resampler.SetTransform(outTx)

	return resampler.Execute(moving), R




def BSplineTransformInitializer2(fixed, moving, par):
	"""
	Reference: SimpleITK
	https://simpleitk.readthedocs.io/en/master/link_ImageRegistrationMethodBSpline2_docs.html
	
	Parameters
	----------
	fixed : ITK array
		Input reference volume.
	moving : ITK array
		Input volume to be aligned.
	par : Dictionary
	
		par['SetMetricAsMattesMutualInformation'] = 50
		par['convergenceMinimumValue'] = 1e-4
		par['convergenceWindowSize'] = 5
		int(par['SetDefaultPixelValue']) = 1

	Returns
	-------
	array
		Array to be reshaped.
	R : object
		Registration info.

	"""
	def command_iteration(method):
		print(
		   f"{method.GetOptimizerIteration():3} "
			+ f"= {method.GetMetricValue():10.5f}"
		)
		print("\t#: ", len(method.GetOptimizerPosition()))


	def command_multi_iteration(method):
		print("--------- Resolution Changing ---------")

	transformDomainMeshSize = [10] * moving.GetDimension()
	tx = sitk.BSplineTransformInitializer(fixed, transformDomainMeshSize)
	
	print("Initial Parameters:")
	print(tx.GetParameters())
	
	R = sitk.ImageRegistrationMethod()
	R.SetMetricAsMattesMutualInformation(int(par['SetMetricAsMattesMutualInformation']))
	R.SetOptimizerAsGradientDescentLineSearch(
		5.0, 100, convergenceMinimumValue=float(par['convergenceMinimumValue']), \
			convergenceWindowSize=int(par['convergenceWindowSize'])
	)
	R.SetOptimizerScalesFromPhysicalShift()
	R.SetInitialTransform(tx)
	R.SetInterpolator(sitk.sitkLinear)
	
	R.SetShrinkFactorsPerLevel([6, 2, 1])
	R.SetSmoothingSigmasPerLevel([6, 2, 1])
	
	R.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(R))
	R.AddCommand(
	    sitk.sitkMultiResolutionIterationEvent, lambda: command_multi_iteration(R)
	)
	
	outTx = R.Execute(fixed, moving)
	
	print("-------")
	print(outTx)
	print(f"Optimizer stop condition: {R.GetOptimizerStopConditionDescription()}")
	print(f" Iteration: {R.GetOptimizerIteration()}")
	print(f" Metric value: {R.GetMetricValue()}")
	
	sitk.WriteTransform(outTx, sys.argv[3])
	
	
	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(int(par['SetDefaultPixelValue']))
	resampler.SetTransform(outTx)
	
	return resampler.Execute(moving), R

def DemonsRegistration1(fixed, moving, par):
	"""
	Reference: SimpleITK
	
	https://simpleitk.readthedocs.io/en/master/link_DemonsRegistration1_docs.html

	Parameters
	----------
	fixed : itk array
		Input reference volume.
	moving : itk arary
		Input volume to be registered.
	par : Dictionary
		par['SetNumberOfHistogramLevels'] = 1024
		par['SetNumberOfMatchPoints'] = 7
		par['SetNumberOfIterations'] = 50
		par['SetStandardDeviations'] = 1.0
		par['SetDefaultPixelValue'] = 1

	Returns
	-------
	Registered data.

	"""

	def command_iteration(filter):
		print(f"{filter.GetElapsedIterations():3} = {filter.GetMetric():10.5f}")


	matcher = sitk.HistogramMatchingImageFilter()
	matcher.SetNumberOfHistogramLevels(int(par['SetNumberOfHistogramLevels']))
	matcher.SetNumberOfMatchPoints(int(par['SetNumberOfMatchPoints']))
	matcher.ThresholdAtMeanIntensityOn()
	moving = matcher.Execute(moving, fixed)
	
	# The basic Demons Registration Filter
	# Note there is a whole family of Demons Registration algorithms included in
	# SimpleITK
	demons = sitk.DemonsRegistrationFilter()
	demons.SetNumberOfIterations(int(par['SetNumberOfIterations']))
	# Standard deviation for Gaussian smoothing of displacement field
	demons.SetStandardDeviations(float(par['SetStandardDeviations']))
	
	demons.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(demons))
	
	displacementField = demons.Execute(fixed, moving)
	
	print("-------")
	print(f"Number Of Iterations: {demons.GetElapsedIterations()}")
	print(f" RMS: {demons.GetRMSChange()}")
	
	outTx = sitk.DisplacementFieldTransform(displacementField)
	
	#sitk.WriteTransform(outTx, sys.argv[3])


	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(int(par['SetDefaultPixelValue']))
	resampler.SetTransform(outTx)

	return resampler.Execute(moving), demons


def DemonsRegistration2(fixed, moving, par):
	"""
	Reference: SimpleITK
	
	https://simpleitk.readthedocs.io/en/master/link_DemonsRegistration2_docs.html

	Parameters
	----------
	fixed : itk array
		Input reference volume.
	moving : itk arary
		Input volume to be registered.
	par : Dictionary
		par['SetNumberOfHistogramLevels'] = 1024 or 128 if 8bit
		par['SetNumberOfMatchPoints'] = 7
		par['SetNumberOfIterations'] = 200
		par['SetStandardDeviations'] = 1.0
		par['SetDefaultPixelValue'] = 1

	Returns
	-------
	Registered data.

	"""


	def command_iteration(filter):
		print(f"{filter.GetElapsedIterations():3} = {filter.GetMetric():10.5f}")

	
	matcher = sitk.HistogramMatchingImageFilter()
	if fixed.GetPixelID() in (sitk.sitkUInt8, sitk.sitkInt8):
	    matcher.SetNumberOfHistogramLevels(int(par['SetNumberOfHistogramLevels']))
	else:
	    matcher.SetNumberOfHistogramLevels(int(par['SetNumberOfHistogramLevels']))
	matcher.SetNumberOfMatchPoints(int(par['SetNumberOfMatchPoints']))
	matcher.ThresholdAtMeanIntensityOn()
	moving = matcher.Execute(moving, fixed)
	
	# The fast symmetric forces Demons Registration Filter
	# Note there is a whole family of Demons Registration algorithms included in
	# SimpleITK
	demons = sitk.FastSymmetricForcesDemonsRegistrationFilter()
	demons.SetNumberOfIterations(int(par['SetNumberOfIterations']))
	# Standard deviation for Gaussian smoothing of displacement field
	demons.SetStandardDeviations(float(par['SetDefaultPixelValue']))
	
	demons.AddCommand(sitk.sitkIterationEvent, lambda: command_iteration(demons))
	"""
	To be implemented
	if len(sys.argv) > 4:
	    initialTransform = sitk.ReadTransform(sys.argv[3])
	    sys.argv[-1] = sys.argv.pop()
	
	    toDisplacementFilter = sitk.TransformToDisplacementFieldFilter()
	    toDisplacementFilter.SetReferenceImage(fixed)
	
	    displacementField = toDisplacementFilter.Execute(initialTransform)
	
	    displacementField = demons.Execute(fixed, moving, displacementField)
	
	else:
	"""
	displacementField = demons.Execute(fixed, moving)

	print("-------")
	print(f"Number Of Iterations: {demons.GetElapsedIterations()}")
	print(f" RMS: {demons.GetRMSChange()}")
	
	outTx = sitk.DisplacementFieldTransform(displacementField)

	resampler = sitk.ResampleImageFilter()
	resampler.SetReferenceImage(fixed)
	resampler.SetInterpolator(sitk.sitkLinear)
	resampler.SetDefaultPixelValue(int(par['SetDefaultPixelValue']))
	resampler.SetTransform(outTx)

	return resampler.Execute(moving), demons

