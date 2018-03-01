import subprocess
import pandas as pd
from time import time
import multiprocessing as mp


def _cmdline(inchi, mode):
    cmd = ['WINEDEBUG=-all', 'wine', 'cfm-predict.exe', '"%s"' % inchi]

    cmd = ' '.join(cmd)

    res = subprocess.check_output(cmd, shell=True,
                                   stderr=subprocess.STDOUT,
                                   cwd=r'./' + mode)

    print('Res: %s' % res)
    return res


def split_energies(result):
    result = result.replace('\r', '')
    lines = result.split('\n')
    start = [0, lines.index('energy1'), lines.index('energy2')]
    stop = [start[1], start[2], len(lines)]

    l = []
    for i1, i2 in zip(start, stop):
        output = ''
        for piece in lines[i1 + 1: i2]:
            output += piece + '\n'
        l.append(output.strip())

    return l


# Mode can be positive ('+' or anything starting with 'p') or negative ('-' or 
# anything starting with 'n')
def predict(inchi, mode, energy=None):
    if mode == '+' or mode.lower()[0] == 'p':
        m = 'pos_cfm_id'
    elif mode == '-' or mode.lower()[0] == 'n':
        m = 'neg_cfm_id'
    else:
        print('Error. Unknown mode \"' + mode + '\".')
        return None
    result = _cmdline(inchi, m)
    if energy is None:
        return result.strip()
    else:
        return specify_energy(result, energy)


def _process(inchi):
    # Predict MSMS
    pos = predict(inchi, '+')
    neg = predict(inchi, '-')

    # Process
    row = [inchi]
    row.extend(split_energies(pos))
    row.extend(split_energies(neg))

    return row


def _process_all_mp(inchis, max_proc_per_cpu):
    p = mp.Pool(processes=mp.cpu_count() * max_proc_per_cpu)
    rows = p.map(_process, inchis)
    return rows


def _process_all_sp(inchis):
    rows = []
    for inchi in inchis:
        rows.append(_process(inchi))
    return rows


def process_all(input, output, mp=False, max_proc_per_cpu=5):
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


if __name__ == '__main__':
    input = './testing/test_small.txt'
    output = 'properties.csv'

    t = time()

    # mp=True for multiprocessing
    process_all(input, output, mp=True)

    print('Time taken: %.1f sec' % (time() - t))

