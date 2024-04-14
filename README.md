# timeit_compare

A method based on timeit that can help you to call timeit.timeit for several
statements and provide comparison results.

------------------------------

## Installation

You can run the following command to install the package

```
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
This problem can be easily solved by the following method:

```python 
from timeit import timeit

print(timeit(sum1))
print(timeit(sum2))
print(timeit(sum3))
print(timeit(sum4))
print(timeit(sum5))
```

and get the results like:

```
3.2710195999825373
2.050656799983699
0.4511557999649085
2.5759165000054054
0.066161299997475
```

Calling timeit multiple times and printing the results makes me feel 
troublesome, and the results seem to be not intuitive.

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

## Contact

If you have any suggestions, please contact me at 
[23S112099@stu.hit.edu.cn](mailto:23S112099@stu.hit.edu.cn).

------------------------------

## End