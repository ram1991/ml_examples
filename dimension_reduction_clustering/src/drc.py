#!/usr/bin/python

import numpy as np
from sklearn.cluster import KMeans
from sklearn.cluster import SpectralClustering
from sklearn.manifold import spectral_embedding
import sklearn.metrics

#	Initialization
np.set_printoptions(precision=4)
np.set_printoptions(threshold=np.nan)
np.set_printoptions(linewidth=300)


def eig_sorted(X):
	D,V = np.linalg.eig(X)	
	lastV = None
	sort_needed = False
	for m in D:
		if m > lastV and lastV != None:
			sort_needed = True
			#print 'Sort needed : \t' , m, lastV
		lastV = m
	
	if sort_needed:
		idx = D.argsort()[::-1]   
		D = D[idx]
		V = V[:,idx]	

	return [V,D] 


def drc(X, k, Gamma=0.5):	# X = data (n,d), k = num of clusters, gamma = 1/sigma^2
	n = X.shape[0]
	d = X.shape[1]

	A = np.eye(d)
	H = np.eye(n) - (1.0/n)*np.ones((n,n))
	U_converged = False
	delta = 0.001
	output = {}
	
	
	##	Calculate initial U
	C = sklearn.metrics.pairwise.rbf_kernel(X, gamma=Gamma)
	U = spectral_embedding(C, n_components=k)
	clf = KMeans(n_clusters=k)
	output['init_allocation'] = clf.fit_predict(U)
		
	while U_converged == False:
		for rep in range(20):
			part_1 = np.linalg.inv(A + delta*np.eye(d))
			part_2 = X.T.dot(H).dot(U).dot(U.T).dot(H).dot(X)
			n_1 = np.linalg.norm(part_1,'fro');
			n_2 = np.linalg.norm(part_2,'fro');
			lmbda = n_1/n_2;
			#lmbda = 1;
				
			for count in range(10):
				FI = part_1 - lmbda*np.power(1.1,count+1)*part_2
				#print '\t\tpart 1 size : ', str(np.linalg.norm(part_1))
				#print '\t\tpart 2 size : ', str(np.linalg.norm(lmbda*np.power(1.1,count+1)*part_2))
		
				V,D = eig_sorted(FI)
				reduced_dim = np.sum(D < 0)
			
				if(reduced_dim < 1):
					count += 1
				else:
					#print 'broke : ' + str(count)
					break;
			
			L = V[:,-reduced_dim:]
			new_A = L.dot(L.T)	
		
			if(np.linalg.norm(new_A - A) < 0.001*np.linalg.norm(A)): break;
			else: A = new_A
		
	
		embed_dim = k
		if(reduced_dim < k): embed_dim = reduced_dim
	
		C = sklearn.metrics.pairwise.rbf_kernel(X.dot(L), gamma=Gamma)
		U_new = spectral_embedding(C, n_components=embed_dim)
	
	
		if(np.linalg.norm(U_new[:,0:k] - U) < 0.001*np.linalg.norm(U)): 
			U_converged = True
			output['allocation'] = allocation
			output['L'] = L
	
		U = U_new[:,0:k]
		clf = KMeans(n_clusters=k)
		allocation = clf.fit_predict(U)
	

	return output


#np.trace(U.T.dot(H).dot(X).dot(A).dot(X.T).dot(H).dot(U))
#np.trace(U.T.dot(H).dot(X).dot(np.eye(4)).dot(X.T).dot(H).dot(U))

