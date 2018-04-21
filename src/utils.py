# source = [ [0.9, 4.72, 9.9, 2.3], [5.1, 2.0, 3.1, 8.36] ]
# source = [ [1, 1, 7, 5], [2, 4, 6, 2] ]
# source = [ [(2, 2), (6, 4)], [(2, 4), (6, 2)] ]
source = [ [(0, 2), (2, 2)], [(0, 0), (2, 4)] ]

handlers = {}

eps = 1
bound = 10

def generate_source(n):
	global source, bound
	rand = lambda : randint(0, bound)
	source = [ [(rand(), rand()), (rand(), rand())] for i in range(n) ]