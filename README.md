# timeit_compare

Based on the timeit library, timeit_compare can time multiple statements and 
provide comparison results.

------------------------------

## Installation

You can run the following command to install the package.

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

You can also perform the following operations to obtain specific values:

```python
from timeit_compare import Compare

cmp = Compare()
for func in sum1, sum2, sum3, sum4, sum5:
    cmp.add_timer(func)
cmp.run()
# cmp.print_results()

result = cmp.get_result(0)  # get the result of the timer with index 0
print(
    result.time, result.repeat, result.number,
    result.mean, result.median, result.min, result.max, result.std,
    result.error, sep='\n'
)
# [3.3324892420678126e-06, 3.175742677501652e-06, 3.2153616044376503e-06, 3.267199346172507e-06, 3.2638434747711383e-06]
# 5
# 24405
# 3.2509272689901518e-06
# 3.2638434747711383e-06
# 3.175742677501652e-06
# 3.3324892420678126e-06
# 5.916418598334957e-08
# None

fastest = cmp.get_fastest()  # get the result of the fastest timer
print(fastest.index)  # 4
```

In a command line interface, call as follows:

```commandline
python -m timeit_compare -s "n = 100" "s = 0;for i in range(1, n + 1):;    s += i" "sum(range(1, n + 1))" "(1 + n) * n // 2"
```

Run the following command for help:

```commandline
python -m timeit_compare -h
```

------------------------------

## Contact

If you have any suggestions, please contact me at
[23S112099@stu.hit.edu.cn](mailto:23S112099@stu.hit.edu.cn).

------------------------------

## End