# timeit_compare

Conveniently measure and compare the execution times of multiple statements.

---

## Installation

To install the package, run the following command:

```commandline
pip install timeit_compare
```

---

## Usage

Here is a simple example from the timeit library documentation:

```pycon
>>> from timeit_compare import cmp
>>> cmp(
...     "'-'.join(str(n) for n in range(100))",
...     "'-'.join([str(n) for n in range(100)])",
...     "'-'.join(map(str, range(100)))"
... )
timing now...
|████████████| 21/21 completed
                                      Table. Comparison Results (unit: s)                                      
───────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Idx            Mean ↓            Median    Min      Max     Stdev                     Stmt                   
───────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1    5.9e-6   75.7%   █████▎    5.9e-6   5.9e-6   6.0e-6   3.8e-8   '-'.join([str(n) for n in range(100)])  
   2    7.3e-6   93.4%   ██████▌   7.3e-6   7.2e-6   7.4e-6   7.6e-8   '-'.join(map(str, range(100)))          
   0    7.8e-6   100.%   ███████   7.8e-6   7.7e-6   8.0e-6   1.1e-7   '-'.join(str(n) for n in range(100))    
───────────────────────────────────────────────────────────────────────────────────────────────────────────────
7 runs, 10290 loops each, total time 1.509s                                                                    
```

In a command line interface, call as follows:

```commandline
python -m timeit_compare - "'-'.join(str(n) for n in range(100))" - "'-'.join([str(n) for n in range(100)])" - "'-'.join(map(str, range(100)))"
```

---

## help

```commandline
usage: python -m timeit_compare [-h] [-v] [- STMT [STMT ...]] [-s [SETUP ...]] [-r REPEAT] [-n NUMBER] [-t TOTAL_TIME] [-w WARMUPS] [--no-progress] [--sort-by {mean,median,min,max,stdev}]
                                [--no-sort] [--reverse] [-p PRECISION] [--percentage [{mean,median,min,max,stdev} ...]] [-f FILE]

options:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -, --stmt STMT [STMT ...]
                        statement to be timed. A multi-line statement can be given by passing multiple strings simultaneously in an argument.
  -s, --setup [SETUP ...]
                        statement to be executed once initially for the last --stmt argument, if there are no --stmt arguments before this, it indicates the default setup statement for all --stmt
                        (default: 'pass'). A multi-line statement is processed in the same way as --stmt.
  -r, --repeat REPEAT   how many times to repeat the timers (default: 7).
  -n, --number NUMBER   how many times to execute statement (default: estimated by -t).
  -t, --total-time TOTAL_TIME
                        if specified and no -n greater than 0 is specified, it will be used to estimate a -n so that the total execution time (in seconds) of all statements is approximately equal
                        to this value (default: 1.5).
  -w, --warmups WARMUPS
                        how many times to warm up the timers (default: 1).
  --no-progress         no progress bar.
  --sort-by {mean,median,min,max,stdev}
                        statistic for sorting the results (default: 'mean').
  --no-sort             do not sort the results.
  --reverse             sort the results in descending order.
  -p, --precision PRECISION
                        digits precision of the results, ranging from 1 to 8 (default: 2).
  --percentage [{mean,median,min,max,stdev} ...]
                        statistics showing percentage (default: same as --sort-by).
  -f, --file FILE       prints the results to a stream (default: the current sys.stdout)
```
