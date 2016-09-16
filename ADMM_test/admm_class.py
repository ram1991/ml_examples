#!/usr/bin/python

import numpy as np
from scipy.optimize import minimize
from StringIO import StringIO
from sklearn.preprocessing import normalize
import pdb


class exponential_solver:
	def __init__(self, db, iv, jv):
		self.db = db
		self.iv = iv
		self.jv = jv
		self.zi = 0
		self.zj = 0

		self.optimal_val = 0
		self.gamma_array = 0

		self.W_shape = db['W_matrix'].shape
		self.wi = self.W_shape[0]
		self.wj = self.W_shape[1]

		self.matrix_gap = 0		# measures the distance between W , Z matrix
		self.last_matrix_gap = 0
		self.learning_rate = 1

		self.tmp_count = 0

	def create_gamma_ij(self, db, y_tilde, i, j):
		if type(self.gamma_array) == type(0):
			return create_gamma_ij(db, self.y_tilde, i, j)
		else:
			return self.gamma_array[i,j]

	def create_A_ij_matrix(i, j):
		db = self.db
		x_dif = db['data'][i] - db['data'][j]
		x_dif = x_dif[np.newaxis]
		return np.dot(np.transpose(x_dif), x_dif)

	def Lagrange_W(self, W):
		db = self.db
		Z = db['Z_matrix']
		L1 = db['L1']
		L2 = db['L2']
		Wsh = self.W_shape

		W2 = W.reshape(Wsh)
		eye_matrix = np.eye(self.wj)

		#	Setting up the cost function
		cost_foo = 0
		for i in self.iv:
			for j in self.jv:
				
				x_dif = db['data'][i] - db['data'][j]
				x_dif = x_dif[np.newaxis]
			
				gamma_ij = self.create_gamma_ij(db, 0, i, j)
				cost_foo = cost_foo - gamma_ij*np.exp(-x_dif.dot(W2).dot(W2.T).dot(x_dif.T))

		Lagrange = np.trace(L1.dot(W2.T.dot(Z) - eye_matrix)) + np.sum(L2.T*(W2 - Z))
		term1 = ( Z.T.dot(W2) - eye_matrix )
		term2 =  W2 - Z 	
		Aug_lag = np.sum(term1*term1) + np.sum(term2*term2)
		foo = cost_foo + Lagrange + Aug_lag
	
		return foo

	def calc_lagrange_results(self, L):
		W = self.db['W_matrix']
		Z2 = self.db['Z_matrix']
		Z_shape = Z2.shape
		eye_matrix = np.eye(Z_shape[1])

		L1 = L[0:self.zj,:]
		L2 = L[self.zj:,:].T


		#	Setting up the cost function
		cost_foo = 0

		Lagrange = np.trace(L1.dot(W.T.dot(Z2) - eye_matrix)) + np.sum(L2.T*(W - Z2))
		term1 = ( Z2.T.dot(W) - eye_matrix )
		term2 =  W - Z2 	
		Aug_lag = np.sum(term1*term1) + np.sum(term2*term2)

		foo = cost_foo + Lagrange + Aug_lag
		return foo

	def Lagrange_Z(self, Z):
		W = self.db['W_matrix']
		L1 = self.db['L1']
		L2 = self.db['L2']

		Z_shape = self.db['Z_matrix'].shape
		Z2 = Z.reshape(Z_shape)

		eye_matrix = np.eye(Z_shape[1])
	
		#	Setting up the cost function
		cost_foo = 0

		Lagrange = np.trace(L1.dot(W.T.dot(Z2) - eye_matrix)) + np.sum(L2.T*(W - Z2))
		term1 = ( Z2.T.dot(W) - eye_matrix )
		term2 =  W - Z2 	
		Aug_lag = np.sum(term1*term1) + np.sum(term2*term2)

		foo = cost_foo + Lagrange + Aug_lag
		return foo

	def calc_dual(self):
		db = self.db
		Z = db['Z_matrix']
		W = db['W_matrix']

		A = np.append(Z.T, np.eye( self.zi ), axis=0)
		B = np.append(np.zeros(Z.T.shape), np.eye( self.zi ), axis=0)
		C = np.append(np.eye(self.zj), np.zeros(Z.shape), axis=0)

		if self.matrix_gap > self.last_matrix_gap:
			self.learning_rate = self.learning_rate*0.9

		self.last_matrix_gap = self.matrix_gap

		db['L'] = db['L'] + self.learning_rate*(A.dot(W)-B.dot(Z)-C)
		db['L1'] = db['L'][0:self.zj,:]
		db['L2'] = db['L'][self.zj:,:].T

		#L = L + alpha*(A.dot(W)-B.dot(Z)-C)
		#L1 = db['L'][0:zj,:]
		#L2 = db['L'][zj:,:].T
		#return {'L':L, 'L1':L1, 'L2':L2}

	def calc_z_cost(self,Z):
		db = self.db
		W = db['W_matrix']
		L1 = db['L1']
		L2 = db['L2']
		I = np.identity(db['q'])

		WZ_I = W.T.dot(Z) - I
		W_Z = W- Z
		magnitude = np.trace(L1.dot(WZ_I)) + np.trace(L2.dot(W_Z)) + np.sum(WZ_I*WZ_I) + np.sum(W_Z*W_Z)

		return magnitude

	def calc_cost(self,W):
		db = self.db
		Z = db['Z_matrix']
		L1 = db['L1']
		L2 = db['L2']
		I = np.identity(db['q'])

		magnitude = 0
		for i in self.iv:
			for j in self.jv:
				
				x_dif = db['data'][i] - db['data'][j]
				x_dif = x_dif[np.newaxis]
			
				gamma_ij = self.create_gamma_ij(db, 0, i, j)
				current_term = gamma_ij*np.exp(-x_dif.dot(W).dot(W.T).dot(x_dif.T))
				magnitude = magnitude - current_term


		WZ_I = W.T.dot(Z) - I
		W_Z = W- Z
		magnitude = magnitude + np.trace(L1.dot(WZ_I)) + np.trace(L2.dot(W_Z)) + np.sum(WZ_I*WZ_I) + np.sum(W_Z*W_Z)

		return magnitude

	def w_gradient(self, W):
		db = self.db
		Z = db['Z_matrix']
		L1 = db['L1']
		L2 = db['L2']
		I = np.identity(db['q'])

		dL_dW_1 = 0
		magnitude = 0
		for i in self.iv:
			for j in self.jv:
				
				x_dif = db['data'][i] - db['data'][j]
				x_dif = x_dif[np.newaxis]
			
				gamma_ij = self.create_gamma_ij(db, 0, i, j)
				current_term = gamma_ij*np.exp(-x_dif.dot(W).dot(W.T).dot(x_dif.T))
				magnitude = magnitude - current_term

				dL_dW_1 = dL_dW_1 + (x_dif.T.dot(x_dif).dot(W))*current_term

		dL_dW_2 = Z.dot(L1) + L2.T + 2*Z.dot(Z.T.dot(W) - I)
		dL_dW = dL_dW_1 + dL_dW_2

		WZ_I = W.T.dot(Z) - I
		W_Z = W- Z
		magnitude = magnitude + np.trace(L1.dot(WZ_I)) + np.trace(L2.dot(W_Z)) + np.sum(WZ_I*WZ_I) + np.sum(W_Z*W_Z)

		return {'magnitude':magnitude, 'dL_dW':dL_dW}


	def w_optimize(self):
		db = self.db
		W = db['W_matrix']
		Z = db['Z_matrix']
		L1 = db['L1']
		L2 = db['L2']
		alpha = 0.5
		W_converges = False

		while not W_converges:

			W_grad = self.w_gradient(W)
			new_W = W - alpha*W_grad['dL_dW']
			new_cost = self.calc_cost(new_W)

			while new_cost > W_grad['magnitude'] and alpha > 0.0001:
				alpha = alpha * 0.8
				new_W = W - alpha*W_grad['dL_dW']
				new_cost = self.calc_cost(new_W)
					
			#alpha = alpha*1.2	
			W = new_W
			if alpha < 0.0001: W_converges = True
			if(np.sum(np.abs(W_grad['dL_dW']))/np.abs(np.sum(W)) < 0.001): W_converges = True

			if self.tmp_count > 200:
				import pdb; pdb.set_trace()

		db['W_matrix'] = W

	def z_gradient(self, Z):
		db = self.db
		W = db['W_matrix']
		L1 = db['L1']
		L2 = db['L2']
		I = np.identity(db['q'])

		WZ_I = W.T.dot(Z) - I
		W_Z = W - Z

		dL_dZ = W.dot(L1.T) - L2.T + 2*W.dot(WZ_I) - 2*(W - Z)
		magnitude = np.trace(L1.dot(WZ_I)) + np.trace(L2.dot(W_Z)) + np.sum(WZ_I*WZ_I) + np.sum(W_Z*W_Z)

		return {'magnitude':magnitude, 'dL_dZ':dL_dZ}


	def z_optimize(self):
		db = self.db
		W = db['W_matrix']
		Z = db['Z_matrix']
		L1 = db['L1']
		L2 = db['L2']
		alpha = 0.5
		Z_converges = False

		while not Z_converges:
			#import pdb; pdb.set_trace()

			Z_grad = self.z_gradient(Z)
			new_Z = Z - alpha*Z_grad['dL_dZ']
			new_cost = self.calc_z_cost(new_Z)

			while new_cost > Z_grad['magnitude'] and alpha > 0.0001:
				alpha = alpha * 0.8
				new_Z = Z - alpha*Z_grad['dL_dZ']
				new_cost = self.calc_cost(new_Z)
					
			#alpha = alpha*1.2	
			Z = new_Z
			if alpha < 0.0001: Z_converges = True
			if(np.sum(np.abs(Z_grad['dL_dZ']))/np.sum(np.abs(Z)) < 0.001): Z_converges = True

			#print new_cost, alpha, Z_converges
			#import pdb; pdb.set_trace()

		db['Z_matrix'] = Z





	def run(self):	
		db = self.db

		self.zi = db['Z_matrix'].shape[0]
		self.zj = db['Z_matrix'].shape[1]

		loop_count = 0
		stay_in_loop = True

		while stay_in_loop:
			#result_w = minimize(self.Lagrange_W, db['W_matrix'], method='nelder-mead', options={'xtol': 1e-4, 'disp': False})
			#db['W_matrix'] = result_w.x.reshape(db['W_matrix'].shape)

			##result_w = minimize(self.Lagrange_W, db['W_matrix'], method='nelder-mead', options={'xtol': 1e-4, 'disp': False,'maxiter':2000})
			##result_w = minimize(self.Lagrange_W, db['W_matrix'], method='BFGS', options={'disp': False}) #nelder-mead, BFGS
			##result_w = minimize(self.Lagrange_W, db['W_matrix'], method='CG', options={'disp': False}) #nelder-mead, BFGS
			##pdb.set_trace()
			##db['W_matrix'] = normalize(db['W_matrix'], norm='l2', axis=0)
			##pdb.set_trace()
			##db['W_matrix'], r = np.linalg.qr(db['W_matrix'])

			#result_z = minimize(self.Lagrange_Z, db['Z_matrix'], method='nelder-mead', options={'xtol': 1e-4, 'disp': False})
			#db['Z_matrix'] = result_z.x.reshape(db['Z_matrix'].shape)
			##db['Z_matrix'] = normalize(db['Z_matrix'], norm='l2', axis=0)

			self.w_optimize()
			self.z_optimize()
			
		

			result_z = minimize(self.Lagrange_Z, db['Z_matrix'], method='nelder-mead', options={'xtol': 1e-4, 'disp': False})
			db['Z_matrix'] = result_z.x.reshape(db['Z_matrix'].shape)

			self.calc_dual()

			loop_count += 1
			self.matrix_gap = np.abs(np.sum(db['W_matrix'].T.dot(db['Z_matrix']) - np.eye(self.zj)))
			#print '---------' , loop_count, self.matrix_gap, self.learning_rate

			if self.matrix_gap < 0.001: 
				print('Exit base on threshold')
				stay_in_loop = False
			if loop_count > 200: 
				print('Exit base on loop_count')
				stay_in_loop = False







def test_1():		# optimal = 2.4309,  2.4311
	db = {}
	db['data'] = np.array([[3,4,0],[2,4,-1],[0,2,-1]])
	db['Z_matrix'] = np.array([[1,0],[0,1],[0,0]])
	db['W_matrix'] = np.array([[1,1],[1,1],[0,0]])
	db['q'] = db['W_matrix'].shape[1]
	
	db['L1'] = np.array([[1,0], [0,2]])		# q x q
	db['L2'] = np.array([[2,3,1],[0,0,1]])	# q x d
	db['L'] = np.append(db['L1'], db['L2'].T, axis=0)
	
	
	iv = np.array([0])
	jv = np.array([1,2])
	esolver = exponential_solver(db, iv, jv)
	esolver.gamma_array = np.array([[0,1,2,-1]])
	esolver.run()
	
	print esolver.calc_cost(db['W_matrix'])
	pdb.set_trace()


def test_2():
	q = 4		# the dimension you want to lower it to

	fin = open('data_1.csv','r')
	data = fin.read()
	fin.close()

	db = {}
	db['data'] = np.genfromtxt(StringIO(data), delimiter=",")
	db['N'] = db['data'].shape[0]
	db['d'] = db['data'].shape[1]
	db['q'] = q
		
	db['L1'] = np.random.normal(0,10, (db['q'], db['q']) )		# q x q
	db['L2'] = np.random.normal(0,10, (db['q'], db['d']) )	# q x d
	db['L'] = np.append(db['L1'], db['L2'].T, axis=0)

	db['SGD_size'] = 2
	db['sigma'] = np.sqrt(1/2.0)
	
	iv = np.arange(db['N'])
	jv = np.arange(db['N'])

	#i_values = np.random.permutation( np.array(range(db['N'])) )
	#iv = i_values[0:db['SGD_size']]
	#j_values = np.random.permutation( np.array(range(db['N'])) )
	#jv = j_values[0:db['SGD_size']]


	for m in range(10):
		#db['Z_matrix'] = np.random.normal(0,10, (db['d'], db['q']) )
		#db['Z_matrix'] = normalize(db['Z_matrix'], norm='l2', axis=0)
		db['Z_matrix'] = np.array([[0,1,2,-1], [-3,-4,0,2], [1,2,3,1], [1,8,0,0], [-1,-2,2,1]])
		db['Z_matrix'],r = np.linalg.qr( db['Z_matrix'] )
		db['W_matrix'] = db['Z_matrix']

		esolver = exponential_solver(db, iv, jv)
		esolver.gamma_array = np.array([[0,1,2,1,1,2], [3,1,3,4,0,2], [1,2,3,8,5,1], [1,2,3,8,5,1], [1,0,0,8,0,0], [1,2,2,1,5,0]])

		esolver.run()

#		try:
#			esolver.run()
#			esolver.Lagrange_W(db['W_matrix'])
#		except:
#			pass

	import pdb; pdb.set_trace()

def test_3():		# optimal = 2.4309,  2.4311
	db = {}
	db['data'] = np.array([[3,4,0],[2,4,-1],[0,2,-1],[1,1,1]])
	db['Z_matrix'] = np.array([[1,0],[0,1],[0,0]])
	db['W_matrix'] = np.array([[1,1],[1,1],[0,0]])
	db['q'] = db['W_matrix'].shape[1]
	
	db['L1'] = np.array([[1,0], [0,2]])		# q x q
	db['L2'] = np.array([[2,3,1],[0,0,1]])	# q x d
	db['L'] = np.append(db['L1'], db['L2'].T, axis=0)
	
	
	iv = np.array([0])
	jv = np.array([1,2,3])
	esolver = exponential_solver(db, iv, jv)
	esolver.gamma_array = np.array([[0,1,2,-1,2]])
	esolver.run()
	
	print esolver.calc_cost(db['W_matrix'])
	pdb.set_trace()

np.set_printoptions(precision=4)
np.set_printoptions(threshold=np.nan)
np.set_printoptions(linewidth=300)

test_3()
