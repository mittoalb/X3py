import h5py
import numpy as np

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
		b = a.create_dataset('data',data=buff,dtype='float32')
		c = a.create_dataset('data_dark',data=darks,dtype='float32')
		d = a.create_dataset('data_white',data=flats,dtype='float32')
		e = a.create_dataset('theta',data=theta)
