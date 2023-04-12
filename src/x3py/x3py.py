__version__ = "0.0.1"
__author__ = "Alberto Mittone"
__lastrev__ = "Last revision: 04/11/23"

import argparse
import sys


import numpy as np
from itkreg import ITKregister
import glob
from utils import make_dir, distribute_jobs

def main():

	parser = argparse.ArgumentParser(description='3D Xanes Python Processing Tool')
	parser.add_argument('--filename', type=str, help='First file name to be processed',default='tiff')
	args = parser.parse_args()

	#create outname
	tmp = args.filename.split('/')
	folder = '/'.join(tmp[:-1])
	tmp.insert(-1,'corrected')
 	
	ndir = '/'.join(tmp[:-1])
	make_dir(ndir)
	out_name = '/'.join(tmp)
	ext = args.filename.split('.')[-1]

	total = glob.glob(folder + "/*." + ext)
	
	total.sort()
	
	ref_name = total[0]
	print('Using', ref_name, ' as reference dataset\n')
	#total = total - list(args.ref)
	total = total[1:] #removing reference from the list

	print("Processing now: ", total, "files to process")

	#Define main function
	itkr = ITKregister(ref_name)
		
	
	CTdatasets = range(0,int(len(total)))

	def runreg(CTdatasets):
		itkr.ImgProc(CTdatasets)

	for i in CTdatasets:
		print(i)
		runreg(i)
	#distribute_jobs(runreg, CTdatasets)

	#sys.exit(main())

if __name__ == "__main__":
	main()	
