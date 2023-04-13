__version__ = "0.0.1"
__author__ = "Alberto Mittone"
__lastrev__ = "Last revision: 04/11/23"

import argparse
import sys

from itkreg import ITKregister
from config import ProInit
import glob
from utils import make_dir, distribute_jobs
import x3logging
	
def main():

	parser = argparse.ArgumentParser(description='3D Xanes Python Processing Tool')
	parser.add_argument('--filename', type=str, help='First file name to be processed',default='tiff')
	parser.add_argument('--method', type=str, help='Registration method',default='TranslationTransform')
	parser.add_argument('--config', type=str, help='Provide Config file',default='config.json')
	parser.add_argument('--log', type=str, help='Custom log file',default='x3py.log')
	
	
	args = parser.parse_args()

	#create outname
	tmp = args.filename.split('/')
	folder = '/'.join(tmp[:-1])
	tmp.insert(-1,'corrected')
 	
	ndir = '/'.join(tmp[:-1])
	make_dir(ndir)
	ext = args.filename.split('.')[-1]

	total = glob.glob(folder + "/*." + ext)
	total.sort()
	
	if int(len(total)) == 0:
		print('No files found.')
		sys.exit() 
	
	#Set reference and processing data list
	ref_name, total = total[0], total[1:]
	print("Using: ", ref_name, " as reference dataset\n")
	
	x3logging.logger.info("Processing now:\n")
	for i in total: x3logging.logger.info(i)
	
	#Define main function
	extra_args = [ref_name, args.method]
	
	#Initialize config and register
	pI = ProInit(ref_name)
	itkr = ITKregister(extra_args, pI.ReturnParameters())
	
	#Prepare file list
	CTdatasets = range(0,int(len(total)))
	return itkr, CTdatasets

#Prepare the job runner
def runreg(CTdatasets):
	itkr.ImgProc(CTdatasets)


if __name__ == "__main__":
	
	itkr, CTdatasets = main()
	#exit(0)
	distribute_jobs(runreg, CTdatasets)
