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
The fast marching method is a simple form of level-set evolution where only a positive speed term is used to govern the differential equation. 
The resulting level-set contour only grows over time. Practically, this algorithm can be used as an advanced region growing segmentation which is controlled by a speed image.

A good propagation speed image for segmentation is close to zero near object boundaries and relatively high in between. 
In this example, an input feature image is smoothed with an anisotropic diffusion method, then the gradient magnitude is used to produce an edge image. A Gaussian with a parameterized sigma is used during the gradient computation to enable the level-set to slow down near edges. The Sigmoid filter performs a linear transform on the gradient magnitude so that boundaries are near zero and homogeneous regions are close to one. The values for alpha and beta are provided in the testing code. The heuristics used to estimate good values are dependent on the minimum value along a boundary and the mean value of the gradient in the object’s region.

Lastly the fast marching filter is configured with an initial trial point and starting value. Each trial point consists of a tuple for an image index including an optional unsigned starting seed value at the trial point. The trial points are the starting location of the level-set. The output of the fast marching filter is a time-crossing map that indicate the time of arrival of the propagated level-set front. We threshold the result to the region the level-set front propagated through to form the segmented object. A graphical interface can be constructed to show the contour propagation over time, enabling a user to select a the desired segmentation.


Reference:
	
	https://simpleitk.readthedocs.io/en/master/link_FastMarchingSegmentation_docs.html

"""


import SimpleITK as sitk
import sys

def main(args):
    if len(args) < 10:
        print(
            "Usage:",
            "FastMarchingSegmentation",
            "<inputImage> <outputImage> <seedX> <seedY> <Sigma>",
            "<SigmoidAlpha> <SigmoidBeta> <TimeThreshold>",
            "<StoppingTime>"
        )
        sys.exit(1)

    inputFilename = args[1]
    outputFilename = args[2]

    seedPosition = (int(args[3]), int(args[4]))

    sigma = float(args[5])
    alpha = float(args[6])
    beta = float(args[7])
    timeThreshold = float(args[8])
    stoppingTime = float(args[9])

    inputImage = sitk.ReadImage(inputFilename, sitk.sitkFloat32)

    smoothing = sitk.CurvatureAnisotropicDiffusionImageFilter()
    smoothing.SetTimeStep(0.125)
    smoothing.SetNumberOfIterations(5)
    smoothing.SetConductanceParameter(9.0)
    smoothingOutput = smoothing.Execute(inputImage)

    gradientMagnitude = sitk.GradientMagnitudeRecursiveGaussianImageFilter()
    gradientMagnitude.SetSigma(sigma)
    gradientMagnitudeOutput = gradientMagnitude.Execute(smoothingOutput)

    sigmoid = sitk.SigmoidImageFilter()
    sigmoid.SetOutputMinimum(0.0)
    sigmoid.SetOutputMaximum(1.0)
    sigmoid.SetAlpha(alpha)
    sigmoid.SetBeta(beta)
    sigmoidOutput = sigmoid.Execute(gradientMagnitudeOutput)

    fastMarching = sitk.FastMarchingImageFilter()

    seedValue = 0
    trialPoint = (seedPosition[0], seedPosition[1], seedValue)

    fastMarching.AddTrialPoint(trialPoint)

    fastMarching.SetStoppingValue(stoppingTime)

    fastMarchingOutput = fastMarching.Execute(sigmoidOutput)

    thresholder = sitk.BinaryThresholdImageFilter()
    thresholder.SetLowerThreshold(0.0)
    thresholder.SetUpperThreshold(timeThreshold)
    thresholder.SetOutsideValue(0)
    thresholder.SetInsideValue(255)

    result = thresholder.Execute(fastMarchingOutput)

    sitk.WriteImage(result, outputFilename)

    image_dict = {"InputImage": inputImage,
                  "SpeedImage": sigmoidOutput,
                  "TimeCrossingMap": fastMarchingOutput,
                  "Segmentation": result,
                  }
    return image_dict


if __name__ == "__main__":
    return_dict = main(sys.argv)