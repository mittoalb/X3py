import numpy as np




rnd_data = np.random.rand(100,100,100)
en_line = np.arange(10)*0.1
print(en_line)


x3data = np.zeros(shape=[100,100,100,10])

for i in range(0,len(en_line)):
	x3data[:,:,:,i] = rnd_data * en_line[i]
	
print(x3data[50,50,50,:])
