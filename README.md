# timeit_compare

Conveniently measure and compare the execution time of multiple statements.

------------------------------

## Installation

To install the package, run the following command:

```commandline
pip install timeit_compare
```

------------------------------

## Usage

Here is a simple example from the timeit library documentation:

```pycon
>>> from timeit_compare import compare
>>> 
>>> compare(
...     "'-'.join(str(n) for n in range(100))",
...     "'-'.join([str(n) for n in range(100)])",
...     "'-'.join(map(str, range(100)))"
... )
timing now...
|████████████| 21/21 completed
                              Table 1. Comparison Results (unit: s)                              
╭────┬───────────────────────────┬──────────────────────────┬────────┬────────┬────────┬────────╮
│ Id │           Stmt            │          Mean ↓          │ Median │  Min   │  Max   │  Std   │
├────┼───────────────────────────┼────────┬───────┬─────────┼────────┼────────┼────────┼────────┤
│ 1  │ '-'.join([str(n) for n i… │ 6.2e-6 │ 75.3% │ █████▎  │ 6.2e-6 │ 6.2e-6 │ 6.3e-6 │ 3.2e-8 │
│ 2  │ '-'.join(map(str, range(… │ 7.2e-6 │ 87.4% │ ██████▏ │ 7.2e-6 │ 7.2e-6 │ 7.3e-6 │ 2.3e-8 │
│ 0  │ '-'.join(str(n) for n in… │ 8.3e-6 │ 100.% │ ███████ │ 8.3e-6 │ 8.2e-6 │ 8.3e-6 │ 2.3e-8 │
╰────┴───────────────────────────┴────────┴───────┴─────────┴────────┴────────┴────────┴────────╯
7 runs, 9894 loops each, total time 1.504s                                                       
```

The table shows some basic descriptive statistics on the execution time of each
statement for comparison, including mean, median, minimum, maximum, and standard
deviation.

In a command line interface, call as follows:

```commandline
python -m timeit_compare -a "'-'.join(str(n) for n in range(100))" -a "'-'.join([str(n) for n in range(100)])" -a "'-'.join(map(str, range(100)))"
```
