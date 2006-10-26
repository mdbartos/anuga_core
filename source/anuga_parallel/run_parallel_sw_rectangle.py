#!/usr/bin/env python
#########################################################
#
#  Main file for parallel mesh testing.
#
#  This is a modification of the run_parallel_advection.py
# file.
#
#
#  Authors: Linda Stals, Steve Roberts and Matthew Hardy,
# June 2005
#
#
#
#########################################################

import pypar    # The Python-MPI interface
import time

from Numeric import array
# pmesh

from print_stats import print_test_stats, build_full_flag

from anuga.shallow_water import Domain
from parallel_shallow_water import Parallel_Domain


# mesh partition routines
from parallel_meshes import parallel_rectangle


numprocs = pypar.size()
myid = pypar.rank()
processor_name = pypar.Get_processor_name()

M = 50
N = M*numprocs

if myid == 0:
    print 'N == %d' %N

points, vertices, boundary, full_send_dict, ghost_recv_dict =\
        parallel_rectangle(N, M, len1_g=1.0*numprocs, len2_g = 1.0)



domain = Parallel_Domain(points, vertices, boundary,
                         full_send_dict  = full_send_dict,
                         ghost_recv_dict = ghost_recv_dict)

# Make a notes of which triangles are full and which are ghost

tri_full_flag = build_full_flag(domain, ghost_recv_dict)

print 'number of triangles = ', domain.number_of_elements


rect = [ 0.0, 0.0, 1.0*numprocs, 1.0]
## try:
##     domain.initialise_visualiser(rect=rect)
##     domain.visualiser.qcolor['stage'] = (0.0, 0.0, 0.8)
##     domain.visualiser.scale_z['stage'] = 1.0
##     domain.visualiser.scale_z['elevation'] = 0.05
## except:
##     print 'No visualiser'







#Boundaries
from parallel_shallow_water import Transmissive_boundary, Reflective_boundary

T = Transmissive_boundary(domain)
R = Reflective_boundary(domain)


domain.set_boundary( {'left': R, 'right': R, 'bottom': R, 'top': R, 'ghost': None} )
domain.check_integrity()

class Set_Stage:
    """Set an initial condition with constant water height, for x<x0
    """

    def __init__(self, x0=0.25, x1=0.75, y0=0.0, y1=1.0, h=5.0, h0=0.0):
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.h  = h
        self.h0 = h0

    def __call__(self, x, y):
        return self.h0 + self.h*((x>self.x0)&(x<self.x1)&(y>self.y0)&(y<self.y1))

domain.set_quantity('stage', Set_Stage(0.2, 0.4, 0.25, 0.75, 1.0, 0.00))

if myid == 0:
    import time
    t0 = time.time()


# Turn on the visualisation

rect = [0.0, 0.0, 1.0, 1.0]
domain.initialise_visualiser()

domain.default_order = 2
domain.beta_w      = 1.0
domain.beta_w_dry  = 0.2
domain.beta_uh     = 1.0
domain.beta_uh_dry = 0.2
domain.beta_vh     = 1.0
domain.beta_vh_dry = 0.2

#domain.beta_w      = 0.9
#domain.beta_w_dry  = 0.9
#domain.beta_uh     = 0.9
#domain.beta_uh_dry = 0.9
#domain.beta_vh     = 0.9
#domain.beta_vh_dry = 0.9

yieldstep = 0.005
finaltime = 1.0

#Check that the boundary value gets propagated to all elements
for t in domain.evolve(yieldstep = yieldstep, finaltime = finaltime):
    if myid == 0:
        domain.write_time()
    #print_test_stats(domain, tri_full_flag)

if myid == 0:
    print 'That took %.2f seconds' %(time.time()-t0)
    print 'Communication time %.2f seconds'%domain.communication_time
    print 'Reduction Communication time %.2f seconds'%domain.communication_reduce_time
    print 'Broadcast time %.2f seconds'%domain.communication_broadcast_time


pypar.finalize()
