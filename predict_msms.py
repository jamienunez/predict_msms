import subprocess
import pandas as pd
from time import time
import multiprocessing as mp
import argparse


def _cmdline(inchi, mode):
#    cmd = ['cfm-predict.exe', '"%s"' % inchi] # For Windows
    cmd = ['WINEDEBUG=-all', 'wine', 'cfm-predict.exe', '"%s"' % inchi]

    cmd = ' '.join(cmd)

    res = subprocess.check_output(cmd, shell=True,
                                   stderr=subprocess.STDOUT,
                                   cwd=r'./' + mode)
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
def predict(inchi, mode):
    if mode == '+' or mode.lower()[0] == 'p':
        m = 'pos_cfm_id'
    elif mode == '-' or mode.lower()[0] == 'n':
        m = 'neg_cfm_id'
    else:
        print('Error. Unknown mode \"' + mode + '\".')
        return None
    result = _cmdline(inchi, m)
    return result.strip()


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

    # Process results
    cols = ['InChI', 'Pos10V', 'Pos20V', 'Pos40V', 'Neg10V', 'Neg20V',
            'Neg40V']
    df = pd.DataFrame(data=rows, columns=cols)
    df.to_csv(output, index=False)

    return


if __name__ == '__main__':
    
    # Parse input
    parser = argparse.ArgumentParser(description='MS/MS Prediction using CFM-ID')
    parser.add_argument('-i','--input', 
                        help='Input filename with InChIs on separate lines', 
                        required=True)
    parser.add_argument('-o','--output', 
                        help='Output filename (default=\'properties.csv\'',
                        required=False, default='properties.csv')
    parser.add_argument('-m', action='store_true', default=False,
                    dest='multiprocess',
                    help='Use multiprocessing')
    parser.add_argument('-n','--proc', help='Processes per CPU (default=5)',
                        required=False, default=5)
    args = parser.parse_args()

    t = time()

    # Run
    process_all(args.input, args.output, mp=args.multiprocess, max_proc_per_cpu=args.proc)

    print('Time taken: %.1f sec' % (time() - t))
