# -*- coding: utf-8 -*-
"""
Created on Tue Nov 15 10:49:37 2016

@author: nune558
"""

from subprocess import PIPE, Popen
import matplotlib.pyplot as plt
import pandas as pd
from time import time

#%% Functions
def _cmdline(command, mode):
    process = Popen(
        args=command,
        stdout=PIPE,
        shell=True,
        cwd = r'C:\Users\MontyPypi\Documents\work-workspace\predict_msms\\' + mode
    )
    return process.communicate()[0]


def specify_energy(full_result, energy):
    full_result = full_result.replace('\r', '')
    lines = full_result.split('\n')
    start = lines.index('energy' + str(energy)) + 1
    if energy < 2:
        stop = lines.index('energy' + str(energy+1))
    else:
        stop = len(lines)
    output = ''
    for piece in lines[start:stop]:
        output += piece + '\n'
    return output.strip()


# Mode can be positive ('+' or anything starting with 'p') or negative ('-' or 
# anything starting with 'n')
def predict(inchi, mode, energy=None):
    if mode == '+' or mode.lower()[0] == 'p':
        m = 'Positive Mode'
    elif mode == '-' or mode.lower()[0] == 'n':
        m = 'Negative Mode'
    else:
        print 'Error. Unknown mode \"' + mode + '\".'
        return None
    result = _cmdline('cfm-predict.exe ' + inchi, m)
    if energy is None:
        return result.strip()
    else:
        return specify_energy(result, energy)


def _process_all_sp(inchis):
    rows = []
    for inchi in inchis:

        # Predict MSMS
        pos = predict(inchi, '+')
        neg = predict(inchi, '-')

        # Process
        row = [inchi]
        row.extend([specify_energy(pos, x) for x in [0, 1, 2]])
        row.extend([specify_energy(neg, x) for x in [0, 1, 2]])
        rows.append(row)

    return rows


def process_all(input, output, mp=False):
    # Create list of InChIs
    with open(input, 'r') as f:
        inchis = [x.strip() for x in f.readlines()]

    if mp:
        rows = _process_all_mp(inchis, max_proc_per_cpu)
    else:
        rows = _process_all_sp(inchis)
    print rows
    # Process results
    cols = ['InChI', 'Pos10V', 'Pos20V', 'Pos40V', 'Neg10V', 'Neg20V',
            'Neg40V']
    df = pd.DataFrame(data=rows, columns=cols)
    df.to_csv(output, index=False)

    return

#%% DSSTox Predictions
input = './testing/test_small.txt'
output = 'properties.csv'

t = time()

# mp=True for multiprocessing
process_all(input, output, mp=False)

print('Time taken: %.1f min' % ((time() - t) / 60))

