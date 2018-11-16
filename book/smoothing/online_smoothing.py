#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Illustrates the different on-line smoothing algorithms using the
bootstrap filter of the following model:

X_t|X_{t-1}=x_{t-1} ~ N(mu+phi(x_{t-1}-mu),sigma^2)
Y_t|X_t=x_t ~ Poisson(exp(x_t))
as in first example in Chopin and Singh (2014, Bernoulli)

More precisely, we compare different smoothing algorithms for approximating
the smoothing expectation of additive function phit, defined as
phi_t(x_0:t) = sum_{s=0}^t psi_s(x_{s-1},x_s)
see below for a definition of psi_s

See Chapter 11 (smoothing) for more details; in particular Figures 11.2 and
11.3 which were produced by this script.

Warnings:
    * takes about 20min to complete. 
    * if multiprocessing does not work on your machine (see installation notes)
    try to set option nprocs to 1 (line 95)

"""

from __future__ import division, print_function

from matplotlib import pyplot as plt
import numpy as np

import particles
from particles import distributions as dists
from particles import state_space_models as ssm


def psit(t, xp, x):
    """ score of the model (gradient of log-likelihood at theta=theta_0)
    """
    if t == 0:
        return -0.5 / sigma0**2 + \
            (0.5 * (1. - phi0**2) / sigma0**4) * (x - mu0)**2
    else:
        return -0.5 / sigma0**2 + (0.5 / sigma0**4) * \
            ((x - mu0) - phi0 * (xp - mu0))**2

class DiscreteCox_with_addf(ssm.DiscreteCox):
    """ A discrete Cox model:
    Y_t ~ Poisson(e^{X_t})
    X_t - mu = phi(X_{t-1}-mu)+U_t,   U_t ~ N(0,1)
    X_0 ~ N(mu,sigma^2/(1-phi**2))
    """
    def upper_bound_log_pt(self, t):
        return -0.5 * log(2 * np.pi) - log(self.sigma)

    def add_func(self, t, xp, x):
        return psit(t, xp, x)


# set up models, simulate data
nruns = 25  # how many runs for each algorithm
T = 10**4  # sample size
mu0 = 0.  # true parameters
phi0 = 0.9
sigma0 = .5

my_ssm = DiscreteCox_with_addf(mu=mu0, phi=phi0, sigma=sigma0)
true_states, data = my_ssm.simulate(T)
fkmod = ssm.Bootstrap(ssm=my_ssm, data=data)

# plot data
plt.figure()
plt.plot(data)
plt.title('data')

methods = ['ON2', 'naive']
attr_names = {k: k + '_online_smooth' for k in methods}
long_names = {'ON2': r'$O(N^2)$ forward-only',
              'naive': r'naive, $O(N)$ forward-only'}
runs = {}
avg_cpu = {}
Ns = {'ON2': 100, 'naive': 10**4}  # for naive N is rescaled later
for method in methods:
    N = Ns[method]
    if method == 'naive':  
        # rescale N to match CPU time
        pf = particles.SMC(fk=fkmod, N=N, naive_online_smooth=True)
        pf.run()
        Ns['naive'] = int(N * avg_cpu['ON2'] / pf.cpu_time)
        print('rescaling N to %i to match CPU time' % Ns['naive'])
    long_names[method] += r', N=%i' % Ns[method]
    print(long_names[method]) 
    outf = lambda pf: {'result': getattr(pf.summaries, attr_names[method]),
                       'cpu': pf.cpu_time}
    args_smc = {'fk': fkmod, 'nruns': nruns, 'nprocs': 0, 'N': N,
                attr_names[method]: True, 'out_func': outf}
    runs[method] = particles.multiSMC(**args_smc)
    avg_cpu[method] = np.mean([r['cpu'] for r in runs[method]])
    print('average cpu time (across %i runs): %f' %(nruns, avg_cpu[method]))

# Plots
# =====
savefigs = False  # toggle this to save the plots as PDFs
plt.style.use('ggplot')
colors = {'ON2':'gray', 'naive':'black'}

# IQR (inter-quartile ranges) as a function of time: Figure 11.3
plt.figure()
estimates = {method: np.array([r['result'] for r in results])
             for method, results in runs.items()}
plt.xlabel(r'$t$')
plt.ylabel('IQR (smoothing estimate)')
plt.yscale('log')
plt.xscale('log')
for method in methods:
    est = estimates[method]
    delta = np.percentile(est, 75., axis=0) - np.percentile(est, 25., axis=0)
    plt.plot(np.arange(T), delta, colors[method], label=long_names[method])
plt.legend(loc=4)
if savefigs:
    plt.savefig('online_iqr_vs_t_logscale.pdf')

# actual estimates
plt.figure()
mint, maxt = 0, T
miny = np.min([est[:, mint:maxt].min() for est in estimates.values()])
maxy = np.max([est[:, mint:maxt].max() for est in estimates.values()])
inflat = 1.1
ax = [mint, maxt, maxy - inflat * (maxy - miny), miny + inflat * (maxy - miny)]
for i, method in enumerate(methods):
    plt.subplot(1, len(methods), i + 1)
    plt.axis(ax)
    plt.xlabel(r'$t$')
    plt.ylabel('smoothing estimate')
    plt.title(long_names[method])
    est = estimates[method]
    for j in range(nruns):
        plt.plot(est[j, :])
if savefigs:
    plt.savefig('online_est_vs_t.pdf')

plt.show()
