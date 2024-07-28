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
>>> from timeit_compare import cmp
>>> cmp(
...     "'-'.join(str(n) for n in range(100))",
...     "'-'.join([str(n) for n in range(100)])",
...     "'-'.join(map(str, range(100)))"
... )
timing now...
|████████████| 21/21 completed
                               Table. Comparison Results (unit: s)                                
╭─────┬───────────────────────────┬──────────────────────────┬────────┬─────────────────┬────────╮
│ Idx │           Stmt            │          Mean ↓          │ Median │    Min - Max    │ Stdev  │
├─────┼───────────────────────────┼────────┬───────┬─────────┼────────┼────────┬────────┼────────┤
│  1  │ '-'.join([str(n) for n i… │ 6.1e-6 │ 77.4% │ █████▍  │ 6.1e-6 │ 6.0e-6 │ 6.2e-6 │ 7.9e-8 │
│  2  │ '-'.join(map(str, range(… │ 7.4e-6 │ 94.3% │ ██████▋ │ 7.3e-6 │ 7.2e-6 │ 8.1e-6 │ 3.2e-7 │
│  0  │ '-'.join(str(n) for n in… │ 7.9e-6 │ 100.% │ ███████ │ 7.8e-6 │ 7.8e-6 │ 8.0e-6 │ 6.5e-8 │
╰─────┴───────────────────────────┴────────┴───────┴─────────┴────────┴────────┴────────┴────────╯
7 runs, 10057 loops each, total time 1.505s                                                       
```

The table shows some basic descriptive statistics on the execution time of each
statement for comparison, including mean, median, minimum, maximum, and standard
deviation.

In a command line interface, call as follows:

```commandline
python -m timeit_compare - "'-'.join(str(n) for n in range(100))" - "'-'.join([str(n) for n in range(100)])" - "'-'.join(map(str, range(100)))"
```
