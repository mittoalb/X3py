import h5py
import numpy as np
import os
import fabio

def readh5(file_name):
	"""
		Read HDF5 file, return numpy arrays
	"""
	fx = h5py.File(file_name,'r')
	fixed, fxflat, fxdark, theta = fx['/exchange/data'], fx['/exchange/data_white'], fx['/exchange/data_dark'], fx['/exchange/theta']

	#Convert into numpy array
	ar_fixed = np.asarray(fixed)
	ar_fxflat = np.asarray(fxflat)
	ar_fxdark = np.asarray(fxdark)
	
	return ar_fixed, ar_fxflat, ar_fxdark, theta


def writeh5(file_name,buff, darks, flats, theta):
	"""
		Write a HDF5 file. Minimal data structure compatible with tomography reconstructions.
	"""
	with h5py.File(file_name,'w') as f:
		a = f.create_group('exchange')
		a.create_dataset('data',data=buff,dtype='float32')
		a.create_dataset('data_dark',data=darks,dtype='float32')
		a.create_dataset('data_white',data=flats,dtype='float32')
		a.create_dataset('theta',data=theta)
		
def make_dir(fname):
	if not os.path.exists(fname):
		os.system('mkdir ' + fname)
	else:
		pass

import multiprocessing as mp
from contextlib import closing

def distribute_jobs(func,proj):
	"""
	Distribute a func over proj on different cores
	"""
	args = []
	pool_size = int(mp.cpu_count()/2)
	chunk_size = int((len(proj) - 1) / pool_size + 1)
	pool_size = int(len(proj) / chunk_size + 1)
	for m in range(pool_size):
		ind_start = int(m * chunk_size)
		ind_end = (m + 1) * chunk_size
		if ind_start >= int(len(proj)):
			break
		if ind_end > len(proj):
			ind_end = int(len(proj))
		args += [range(ind_start, ind_end)]
	#mp.set_start_method('fork')
	with closing(mp.Pool(processes=pool_size)) as p:
		out = p.map_async(func, proj)
	out.get()
	p.close()		
	p.join()

def readTIFF(file_name):
	return fabio.open(file_name)

def writeTIFF(file_name,data):
	data.write(file_name)
	

def GPURAM():
	"""
	Return the free and total GPU RAM of n devices
	"""
	import nvidia_smi
	
	nvidia_smi.nvmlInit()
	
	deviceCount = nvidia_smi.nvmlDeviceGetCount()
	free_ram = np.zeros(deviceCount)
	total_ram = np.zeros(deviceCount)

	for i in range(deviceCount):
		handle = nvidia_smi.nvmlDeviceGetHandleByIndex(i)
		info = nvidia_smi.nvmlDeviceGetMemoryInfo(handle)
		free_ram[i] = info.free
		total_ram[i] = info.total
		
	nvidia_smi.nvmlShutdown()
	return free_ram, total_ram