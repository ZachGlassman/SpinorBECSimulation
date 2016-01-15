# -*- coding: utf-8 -*-
"""
Simulation Runner - This is a module containing a unified interface
into the 3 simulation types written.  It should be the primary way to interact
with the simulation codes.  It will allow easy comparison of results.

Three types of codes and requirements
Mean Field:
    Number of atoms
    number of samples (truncated wigner)
    c
    tfinal (simulation time)
    pulses
    qu0 (optional)
    magnetic field
Fock State Full Quantum:
   Number of atoms
   c
   mag_time(for magnetic field) not currently implemented
   tauB(magnetic field decay) not currently implemented
   dt (timestep)
   magnetic field
Coherent State full Quantum:
    Number of Atoms
    magnetic field
    magnetization
    magnetic_field range loop
    atom_range loop
    spinor_phase
    n_0
    c (list)
    delta_t (list)
    ndiv (list)
    emw (list)
    n_step (list)

It will provide a unified plotting interface and variable interface
@author: Zachary Glassman
"""

    
from MeanField.MeanFieldSimulation import single_simulation as mean_sim
from FullQuantumFock.FockStateSimulation import fock_sim
from CoherentStateChebyshev.spinorf import solve_system as cheby_sim
import numpy as np
import matplotlib.pyplot as plt
import time as time_mod
import seaborn
import configparser
import argparse

def color_text(text, color):
    """Function color text
    :param data: text to color
    :type data: string
    :param color: color
    :type color: string
    """
    try:
        return getattr(colorama.Fore,color) + text + colorama.Style.RESET_ALL
    except:
        return text


class SimulationResult(object):
    """class to hold results so we can parse different simulation into
    equivalent results"""
    def __init__(self,time,rho_0,std,color, name):
        self.t = time
        self.rho = rho_0
        self.std = std
        self.name = name
        self.col = color

    def plot(self, ax):
        """plot given axis ax"""
        ax.fill_between(self.t,self.rho-self.std,self.rho+self.std, color = self.col, alpha = .2)
        ax.plot(self.t, self.rho, label = self.name, color = self.col)

    def print_information(self):
        print(self.t)
        print(self.rho)


class Simulation(object):
    """Simulation Class is a simulation for a certain set of parameters
    Will automatically use correct factors to compare to real vales"""
    def __init__(self, name, pulses = [], number = False):
        """Inititalize name and all possible parameters set to reasonable values"""
        self.name = name
        self.params = {
            'N': 5000,
            'c': 24,
            'n_samps': 200,
            'magnetic_field': 27,
            'atom_range': 20,
            'mag_range': 20,
            'spinor_phase': 0,
            'n_0': 4998,
            'time_step': 0.001e-3,
            'tauB': 1e-3,
            'total_time': .01,
            'mag_time': 0.015,
            'mag': 0,
        }
        self.pulses = pulses
        self.number = number

        self.fock = False
        self.mean = False
        self.cheby = False
        self.verbose = False

    def run_fock(self):
        """run a fock simulation with the current parameters"""
        if self.verbose:
            print(color_text('Running Fock State Simulation', 'CYAN'))
            ts = time_mod.time()
        time, n0, n0var = fock_sim(self.params['total_time'],
                self.params['time_step'],
                self.params['mag_time'],
                self.params['tauB'],
                int(self.params['N']),
                self.params['c']*4*np.pi,
                self.params['magnetic_field'])
        std = np.sqrt(n0var)
        if not self.number:
            n0 = n0/self.params['N']
            std= std/self.params['N']
        self.fock_res = SimulationResult(time, n0, std, 'red','Fock')
        self.fock = True
        if self.verbose:
            te = time_mod.time()
            print(color_text('Finished Fock State Simulation', 'RED'))
            print('Execution Time: {0:>4.2f}'.format(te-ts))


    def run_mean(self):
        """run a mean field simulation with the current parameters"""
        if self.verbose:
            print(color_text('Running Mean Field Simulation', 'YELLOW'))
            ts = time_mod.time()
        time, mean, std, mw = self.mean_res = mean_sim(int(self.params['N']),
                 int(self.params['n_samps']),
                 self.params['c']*4*np.pi,
                 self.params['total_time'],
                 self.params['magnetic_field'],
                 self.pulses,qu0=0)
        if self.number:
            mean = mean * self.params['N']
            std = std * self.params['N']
        self.mean_res = SimulationResult(time, mean, std, 'blue','Mean')
        self.mean = True
        if self.verbose:
            te = time_mod.time()
            print(color_text('Finished Mean Field Simulation', 'RED'))
            print('Execution Time: {0:>4.2f}'.format(te-ts))

    def run_cheby(self,save = False):
        """run a chebyshev simulation with the current paramters"""
        if self.verbose:
            print(color_text('Running Coherent Simulation', 'MAGENTA'))
            ts = time_mod.time()
        if self.pulses == []:
            dt = .005
            c = [self.params['c']]
            emw = [.277/(np.pi)] #this is also q scaled by pi
            n_step = [int(self.params['total_time']/dt)]
            ndiv = 1
            delta_t = [self.params['total_time']]

        sum_of_means, sum_of_meansq, norm, time = cheby_sim(self.params['magnetic_field']*100,
                  int(self.params['N']),
                  int(self.params['mag']),
                  int(self.params['mag_range']),
                  int(self.params['atom_range']),
                  self.params['spinor_phase'],
                  int(self.params['n_0']),
                  ndiv,
                  delta_t,
                  c,
                  emw,
                  n_step)
        mean = sum_of_means/norm
        meansq = sum_of_meansq/norm
        std = np.sqrt(meansq - mean*mean)
        self.cheby = True
        self.cheby_res = SimulationResult(time, mean,std, 'green', 'Coherent')

        if self.verbose:
            te = time_mod.time()
            print('\n',color_text('Finished Coherent Simulation', 'RED'))
            print('Execution Time: {0:>4.2f}'.format(te-ts))


    def plot(self):
        if not self._has_result:
            print('Cannot plot with no simulation')
        else:
            fig, ax = plt.subplots()
            if self.fock:
                self.fock_res.plot(ax)
            if self.mean:
                self.mean_res.plot(ax)
            if self.cheby:
                self.cheby_res.plot(ax)
            ax.set_xlabel('t (s)')
            if self.number:
                ax.set_ylabel(r'$N_{m_F=0}$')
            else:
                ax.set_ylabel(r'$\rho_0$')
            ax.legend()



    def _has_result(self):
        if self.fock or self.mean or self.cheby:
            return True
        else:
            return False

    def reset(self):
        self.cheby = False
        self.mean = False
        self.fock = False

def main(config,args):
    #keys for configuarion file
    sims = 'Simulation Settings'
    gsp = 'Global Simulation Parameters'
    tw = 'TW Parameters'
    fsp = 'Fock Simulation Parameters'
    cscp = 'Coherent State Chebyshev Parameters'
    #create simultion
    s = Simulation(config[sims].get('Name','sim'))
    if args.verbose == True:
        s.verbose = True
    #loop through each one
    for con in [config[gsp],config[tw],config[fsp],config[cscp]]:
        for key in con:
            s.params[key] = float(con[key])
            if args.verbose == True:
                print('{0} set to {1}'.format(key,con[key]))

    #now run simulations
    if args.verbose == True:
        print(''.join('#' for i in range(20)))
        print('Simulations Set Up - Starting Numerics')
    ts = time_mod.time()
    s.number = True
    if config[sims].getboolean('run_coherent', False):
        s.run_cheby()
    if config[sims].getboolean('run_fock', False):
        s.run_fock()
    if config[sims].getboolean('run_tw', False):
        s.run_mean()
    te = time_mod.time()
    if args.verbose == True:
        mins, secs = divmod(te-ts, 60)
        hours, mins = divmod(mins, 60)
        print(''.join('#' for i in range(20)))
        out_form = 'Total Sim Time {0:02.0f}h:{1:02.0f}m:{2:02.2f}s'
        print(out_form.format(hours,mins,secs))

    if config[sims].getboolean('plot',True):
        s.plot()
        print('Saving Figure','{0}_plot.pdf'.format(s.name))
        plt.savefig('{0}_plot.pdf'.format(s.name))
    if args.verbose == True:
        print(''.join('#' for i in range(20)))
    print('Simulation Complete')
if __name__ == '__main__':
    #add parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-v',
                       dest='verbose',
                       action='store',
                       default = True,
                       help='verbose output (default True)')
    parser.add_argument('-c',
                        dest ='config',
                        action = 'store',
                        help = 'Path to config file',
                        required = True)
    args = parser.parse_args()
    #get configuration
    config = configparser.ConfigParser()

    config.read(args.config)
    main(config, args)
