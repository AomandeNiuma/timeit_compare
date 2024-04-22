# timeit_compare

A method based on timeit that can help you to call timeit.timeit for several
statements and provide comparison results.

------------------------------

## Installation

You can run the following command to install the package

```commandline
pip install timeit_compare
```

------------------------------

## Usage

When using the timeit library, I am always more interested in comparing the
efficiency of several different methods to solve a problem, rather than simply
measuring the running time of a single statement. Here is a simple example.

```python
from functools import reduce
from operator import add

n = 100


def sum1():
    s = 0
    i = 1
    while i <= n:
        s += i
        i += 1
    return s


def sum2():
    s = 0
    for i in range(1, n + 1):
        s += i
    return s


def sum3():
    return sum(range(1, n + 1))


def sum4():
    return reduce(add, range(1, n + 1))


def sum5():
    return (1 + n) * n // 2
```

The functions above are all used to sum numbers from 1 to 100, which one is the
most efficient?  
By using:

```python
from timeit_compare import compare

compare(sum1, sum2, sum3, sum4, sum5)
```

you can easily get the results like:

[![output_example.png](https://raw.githubusercontent.com/AomandeNiuma/timeit_compare/main/output_example.png)](
https://raw.githubusercontent.com/AomandeNiuma/timeit_compare/main/output_example.png)

The output provides detailed results, including the mean, median, minimum,
maximum and standard deviation of each function's running time.

------------------------------

## Release Notes

### Release 1.1.0

1. The results now show the time of one loop in seconds(s), milliseconds(ms),
   microseconds(μs), or nanoseconds(ns) instead of the total time of each
   repetition. The conversion relationship among time units is as follows:

   ```
   1(s) = 10^3(ms) = 10^6(μs) = 10^9(ns)
   ```

2. Now the compare function supports setting parameters setup and globals
   separately for each statement. Keyword parameters setup and globals are
   now used to set the default parameter values for each statement.

   ```python
   from timeit_compare import compare
   
   stmt = '(1 + n) * n // 2'
   compare(
       stmt,
       (stmt, 'n = 100', {}),
       (stmt, '', {'n': 100}),
       setup='n = 100'
   )
   ```

3. If parameter number is not given or is less than or equal to 0, it now
   defaults to a value that makes the total running time not too long. You can
   intentionally set it to a higher value to make the results more accurate.

4. Command line calls are now supported.

   ```commandline
   python -m timeit_compare -s "n = 100" "(1 + n) * n / 2" "sum(range(1, n + 1))"
   ```

   Run the following command for help.

   ```commandline
   python -m timeit_compare -h
   ```

### Release 1.1.2

1. Added a parameter: time, which represents approximate total running time of
   all statements in seconds (default 1.0). When a positive value of number
   parameter is not given, it will be used to estimate number. Ignored when
   number is greater than 0.

2. Corrected the error of representing sample standard deviation as population
   standard deviation.

------------------------------

## Contact

If you have any suggestions, please contact me at
[23S112099@stu.hit.edu.cn](mailto:23S112099@stu.hit.edu.cn).

------------------------------

## End