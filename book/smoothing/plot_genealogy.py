#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plots the genealogical tree generated by a bootstrap filter. Model is 

X_t|X_{t-1}=x_{t-1} ~ N(mu+phi(x_{t-1}-mu), sigma^2)
Y_t|X_t=x_t ~ Poisson(exp(x_t))

See Figure 11.2 for more details. 

"""

from __future__ import division, print_function

from matplotlib import pyplot as plt
import numpy as np
# import seaborn as sb

import particles
from particles import distributions as dists
from particles import state_space_models as ssm

# set up models, simulate and save data
T = 100
mu0 = 0.
phi0 = 0.9
sigma0 = .5  # true parameters
my_ssm = ssm.DiscreteCox(mu=mu0, phi=phi0, sigma=sigma0)
true_states, data = my_ssm.simulate(T)
fkmod = ssm.Bootstrap(ssm=my_ssm, data=data)

# run particle filter, compute trajectories 
N = 100
pf = particles.SMC(fk=fkmod, N=N, store_history=True)
pf.run()
pf.hist.compute_trajectories()

# PLOT
# ====
# sb.set_palette("dark")
plt.style.use('ggplot')
savefigs = False 

plt.figure()
plt.xlabel('t')
for n in range(N):
    plt.plot(pf.hist.B[:, n], 'k')
if savefigs:
    plt.savefig('genealogy.pdf')

plt.show()
