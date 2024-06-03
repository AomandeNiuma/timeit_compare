# timeit_compare

Based on the timeit library, timeit_compare can conveniently measure execution
times of multiple statements and provide some basic descriptive statistics to
compare the results.

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
|████████████| 15/15 completed
                                 Table 1. Comparison Results (unit: s)                                 
╭────┬───────────────────────────┬─────┬──────────────────────────┬────────┬────────┬────────┬────────╮
│ Id │           Stmt            │ Rpt │          Mean ↓          │ Median │  Min   │  Max   │  Std   │
├────┼───────────────────────────┼─────┼────────┬───────┬─────────┼────────┼────────┼────────┼────────┤
│ 1  │ '-'.join([str(n) for n i… │  5  │ 6.2e-6 │ 74.5% │ █████▎  │ 6.2e-6 │ 6.2e-6 │ 6.2e-6 │ 1.3e-8 │
│ 2  │ '-'.join(map(str, range(… │  5  │ 7.2e-6 │ 86.9% │ ██████▏ │ 7.2e-6 │ 7.2e-6 │ 7.2e-6 │ 1.9e-8 │
│ 0  │ '-'.join(str(n) for n in… │  5  │ 8.3e-6 │ 100.% │ ███████ │ 8.3e-6 │ 8.3e-6 │ 8.3e-6 │ 2.0e-8 │
╰────┴───────────────────────────┴─────┴────────┴───────┴─────────┴────────┴────────┴────────┴────────╯
9225 executions for each statement per repetition                                                      
total execution time 1.0007s                                                                           
```

The table shows some basic descriptive statistics on the execution time of each
statement for comparison, including mean, median, minimum, maximum, and standard
deviation.

In a command line interface, call as follows:

```commandline
python -m timeit_compare -a "'-'.join(str(n) for n in range(100))" -a "'-'.join([str(n) for n in range(100)])" -a "'-'.join(map(str, range(100)))"
```
