__version__ = "0.0.1"
__author__ = "Alberto Mittone"
__lastrev__ = "Last revision: 04/11/23"

import argparse
import sys
import os

import numpy as np
import fabio
import itkreg

def main():

	parser = argparse.ArgumentParser(description='3D Xanes Python Processing Tool')
	parser.add_argument('--ref', type=str, help='Reference Image',default='none')
	parser.add_argument('--filename', type=str, help='First file name to be processed',default='tiff')
	args = parser.parse_args()



	#file_name = '/local/data/alberto/raw/P-1C_260.h5'
	out_name = '/local/data/alberto/corrected/P-1C_262.h5'
	
	#reference = '/local/data/alberto/raw/P-1C_258.h5'
	extra_args = []
	itkr = itkreg.ITKregister(args.ref,extra_args)
	itkr.ImgProc(args.filename, out_name)
	
	#sys.exit(main())

if __name__ == "__main__":
	main()	
