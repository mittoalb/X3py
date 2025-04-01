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
Created on Thu Apr 13 11:51:30 2023

@author: amittone
"""
import numpy as np
import os


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
	return free_ram, 




from treelib import Node, Tree, node
import json

def json_2_tree(contents, parent_id=None, tree=None, counter_byref=[0], verbose=False, listsNodeSymbol='+'):
	if tree is None:
		tree = Tree()
		root_id = counter_byref[0]
		if verbose:
			print(f"tree.create_node({'+'}, {root_id})")
		tree.create_node('+', root_id)
		counter_byref[0] += 1
		parent_id = root_id
	if type(contents) == dict:
		for k,v in contents.items():
			this_id = counter_byref[0]
			if verbose:
				print(f"tree.create_node({str(k)}, {this_id}, parent={parent_id})")
			tree.create_node(str(k), this_id, parent=parent_id)
			counter_byref[0]  += 1
			json_2_tree(v , parent_id=this_id, tree=tree, counter_byref=counter_byref, verbose=verbose, listsNodeSymbol=listsNodeSymbol)
	elif type(contents) == list:
		if listsNodeSymbol is not None:
			if verbose:
				print(f"tree.create_node({listsNodeSymbol}, {counter_byref[0]}, parent={parent_id})")
			tree.create_node(listsNodeSymbol, counter_byref[0], parent=parent_id)
			parent_id=counter_byref[0]
			counter_byref[0]  += 1        
		for i in contents:
			json_2_tree(i , parent_id=parent_id, tree=tree, counter_byref=counter_byref, verbose=verbose,listsNodeSymbol=listsNodeSymbol)
	else: #node
		if verbose:
			print(f"tree.create_node({str(contents)}, {counter_byref[0]}, parent={parent_id})")
		tree.create_node(str(contents), counter_byref[0], parent=parent_id)
		counter_byref[0] += 1
	return tree
