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

The table shows some basic descriptive statistics on the execution time of each
statement for comparison, including mean, median, minimum, maximum, and standard
deviation.

In a command line interface, call as follows:

```commandline
python -m timeit_compare - "'-'.join(str(n) for n in range(100))" - "'-'.join([str(n) for n in range(100)])" - "'-'.join(map(str, range(100)))"
```
