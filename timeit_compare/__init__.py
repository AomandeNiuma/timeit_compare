"""
Conveniently measure and compare the execution times of multiple statements.

Python quick usage:
    from timeit_compare import cmp

    cmp(*timers[, setup][, globals][, repeat][, number][, total_time]
        [, warmups][, show_progress][, sort_by][, reverse][, precision]
        [, percentage][, file])

See the function cmp.

Command line usage:
    python -m timeit_compare [-h] [-v] [- STMT [STMT ...]] [-s [SETUP ...]]
        [-r REPEAT] [-n NUMBER] [-t TOTAL_TIME] [-w WARMUPS] [--no-progress]
        [--sort-by {mean,median,min,max,stdev}] [--no-sort] [--reverse]
        [-p PRECISION] [--percentage [{mean,median,min,max,stdev} ...]]
        [-f FILE]

Run 'python -m timeit_compare -h' for command line help.
"""

import sys
import time
from timeit import Timer

from ._output import TimeitResultOutput, ComparisonResultsOutput, progress

# python >= 3.6

__version__ = '1.4.3'

__all__ = ['TimeitResult', 'ComparisonResults', 'compare', 'cmp']

_stats = ('mean', 'median', 'min', 'max', 'stdev')


class TimeitResult(TimeitResultOutput):
    """
    Object with info about the timeit result of a single statement, obtained by
    indexing a ComparisonResults object.

    Contains the following attributes:

    index: the index of the timer in the list of timers
    stmt: timed statement
    repeat: number of times the timer has been repeated
    number: number of times the statement has been executed each repetition
    times: a list of the average times taken to execute the statement once in
        each repetition
    total_time: total execution time of the statement
    mean, median, min, max, stdev: some basic descriptive statistics on the
        execution times
    unreliable: the judgment of whether the result is unreliable. If the worst
        time was more than four times slower than the best time, we consider it
        unreliable
    """

    __slots__ = ('index', 'stmt', 'repeat', 'number', 'times', 'total_time',
                 *_stats, 'unreliable')

    def __init__(self, index, stmt, repeat, number, times, total_time):
        n = len(times)
        if n >= 1:
            mean = sum(times) / n
            sorted_times = sorted(times)
            half_n = n // 2
            if n & 1:
                median = sorted_times[half_n]
            else:
                median = (sorted_times[half_n] + sorted_times[half_n - 1]) / 2
            min_ = sorted_times[0]
            max_ = sorted_times[-1]
        else:
            mean = median = min_ = max_ = None
        if n >= 2:
            stdev = ((sum(i * i for i in times) - n * mean * mean) /
                     (n - 1)) ** 0.5
            unreliable = max_ > min_ * 4
        else:
            stdev = None
            unreliable = False

        self.index = index
        self.stmt = stmt
        self.repeat = repeat
        self.number = number
        self.times = times
        self.total_time = total_time
        self.mean = mean
        self.median = median
        self.min = min_
        self.max = max_
        self.stdev = stdev
        self.unreliable = unreliable

    def __str__(self):
        return self._table(2)

    def print(self, precision=2, file=None):
        """
        Print the result in tabular form.
        :param precision: digits precision of the result, ranging from 1 to 8
            (default: 2).
        :param file: prints the results to a stream (default: the current
            sys.stdout)
        """
        if not isinstance(precision, int):
            raise TypeError(f'precision must be a integer, not '
                            f'{type(precision).__name__!r}')
        if precision < 1:
            precision = 1
        elif precision > 8:
            precision = 8

        if file is not None:
            if not hasattr(file, 'write'):
                raise AttributeError(f"{type(file).__name__!r} object has no "
                                     f"attribute 'write'")
            if not callable(getattr(file, 'write')):
                raise TypeError("The 'write' method of the file must be "
                                "callable")

        print(self._table(precision), file=file)


class ComparisonResults(ComparisonResultsOutput):
    """
    Object returned by the compare function with info about the timeit results
    of all statements.

    Contains the following attributes:

    repeat: number of times the timers has been repeated
    number: number of times the statements has been executed each repetition
    total_time: total execution time of all statements
    unreliable: the judgment of whether any timer's result is unreliable
    """

    __slots__ = ('repeat', 'number', '_results', 'total_time', 'unreliable')

    def __init__(self, repeat, number, results):
        total_time = sum(result.total_time for result in results)
        unreliable = any(result.unreliable for result in results)
        self.repeat = repeat
        self.number = number
        self._results = results
        self.total_time = total_time
        self.unreliable = unreliable

    def __getitem__(self, item):
        if not isinstance(item, int):
            raise TypeError(f'index must be a integer, not '
                            f'{type(item).__name__!r}')
        return self._results[item]

    def __iter__(self):
        return iter(self._results)

    def __reversed__(self):
        return reversed(self._results)

    def __len__(self):
        return len(self._results)

    def __str__(self):
        return self._table('mean', False, 2, {'mean'}, None, None)

    def print(self, sort_by='mean', reverse=False, precision=2, percentage=None,
              include=None, exclude=None, file=None):
        """
        Print the results in tabular form.
        :param sort_by: statistic for sorting the results (default: 'mean'). If
            None is specified, no sorting will be performed.
        :param reverse: whether to sort the results in descending order
            (default: False).
        :param precision: digits precision of the results, ranging from 1 to 8
            (default: 2).
        :param percentage: statistics showing percentage (default: same as
            sort_by).
        :param include: indices of the included results (default: including all
            results).
        :param exclude: indices of the excluded results (default: no results
            excluded).
        :param file: prints the results to a stream (default: the current
            sys.stdout)
        """
        args = self._check_print_args(
            sort_by, reverse, precision, percentage, include, exclude, file,
            len(self._results)
        )
        return self._print(args)

    @staticmethod
    def _check_print_args(sort_by, reverse, precision, percentage, include,
                          exclude, file, _result_num):
        """Internal function."""
        if sort_by is not None:
            sort_by = ComparisonResults._check_stat(sort_by, 'sort_by')

        reverse = bool(reverse)

        if not isinstance(precision, int):
            raise TypeError(f'precision must be a integer, not '
                            f'{type(precision).__name__!r}')
        if precision < 1:
            precision = 1
        elif precision > 8:
            precision = 8

        if percentage is None:
            percentage = sort_by
        if percentage is None:
            percentage = []
        elif isinstance(percentage, str):
            percentage = percentage.replace(',', ' ').split()
        percentage = {
            ComparisonResults._check_stat(stat, 'stat in percentage')
            for stat in percentage
        }

        if include is not None and exclude is not None:
            raise ValueError('include and exclude cannot be specified '
                             'simultaneously')
        if include is not None:
            include = set(include)
            for index in include:
                if not isinstance(index, int):
                    raise TypeError(f'timer index must be a integer, not '
                                    f'{type(index).__name__!r}')
                elif not 0 <= index < _result_num:
                    raise IndexError('timer index out of range')
        elif exclude is not None:
            exclude = set(exclude)
            for index in exclude:
                if not isinstance(index, int):
                    raise TypeError(f'timer index must be a integer, not '
                                    f'{type(index).__name__!r}')

        if file is not None:
            if not hasattr(file, 'write'):
                raise AttributeError(f"{type(file).__name__!r} object has no "
                                     f"attribute 'write'")
            if not callable(getattr(file, 'write')):
                raise TypeError("The 'write' method of the file must be "
                                "callable")

        return sort_by, reverse, precision, percentage, include, exclude, file

    @staticmethod
    def _check_stat(stat, subject):
        """Internal function."""
        if not isinstance(stat, str):
            raise TypeError(f'{subject} must be a string, not '
                            f'{type(stat).__name__!r}')
        stat = stat.lower()
        if stat not in _stats:
            raise ValueError(
                f"{subject} {stat!r} is not optional: must be "
                f"{', '.join(_stats[:-1])}, or {_stats[-1]}")
        return stat

    def _print(self, args):
        """Internal function."""
        table_args, file = args[:-1], args[-1]
        print(self._table(*table_args), file=file)


class _Timer(Timer):
    """Internal class."""

    def __init__(self, index, stmt, setup, globals):
        super().__init__(stmt, setup, time.perf_counter, globals)
        self.index = index
        self.stmt = stmt
        self.times = []
        self.total_time = 0.0

    if sys.version_info >= (3, 11):
        def timeit(self, number):
            try:
                return super().timeit(number)
            except Exception as e:
                e.add_note(f'(timer index: {self.index})')
                raise


def compare(*timers, setup='pass', globals=None, repeat=7, number=0,
            total_time=1.5, warmups=1, show_progress=False):
    """
    Measure the execution times of multiple statements and return comparison
    results.
    :param timers: (stmt, setup, globals) or a single stmt for timeit.Timer.
    :param setup: default setup statement for timeit.Timer (default: 'pass').
    :param globals: default globals for timeit.Timer (default: global namespace
        seen by the caller's frame, if this is not possible, it defaults to {},
        specify globals=globals() or setup instead).
    :param repeat: how many times to repeat the timers (default: 7).
    :param number: how many times to execute statement (default: estimated by
        total_time).
    :param total_time: if specified and no number greater than 0 is specified,
        it will be used to estimate a number so that the total execution time
        (in seconds) of all statements is approximately equal to this value
        (default: 1.5).
    :param warmups: how many times to warm up the timers (default: 1).
    :param show_progress: whether to show a progress bar (default: False).
    :return: A ComparisonResults type object.
    """
    if not isinstance(repeat, int):
        raise TypeError(f'repeat must be a integer, not '
                        f'{type(repeat).__name__!r}')
    if repeat < 1:
        repeat = 1

    if not isinstance(number, int):
        raise TypeError(f'number must be a integer, not '
                        f'{type(number).__name__!r}')
    if number < 0:
        number = 0

    if not isinstance(total_time, (float, int)):
        raise TypeError(f'total_time must be a real number, not '
                        f'{type(total_time).__name__!r}')
    if total_time < 0.0:
        total_time = 0.0

    if not isinstance(warmups, int):
        raise TypeError(f'warmups must be a integer, not '
                        f'{type(warmups).__name__!r}')
    if warmups < 0:
        warmups = 0

    show_progress = bool(show_progress)

    if globals is None:
        try:
            # sys._getframe is not guaranteed to exist in all
            # implementations of Python
            globals = sys._getframe(1).f_globals
        except:
            globals = {}

    all_timers = []
    for index, args in enumerate(timers):
        if isinstance(args, str) or callable(args):
            args = args, setup, globals
        else:
            args = list(args)
            if len(args) < 3:
                args.extend((None,) * (3 - len(args)))
            if args[1] is None:
                args[1] = setup
            if args[2] is None:
                args[2] = globals
        all_timers.append(_Timer(index, *args))

    if show_progress:
        print('timing now...')

    if warmups > 0:
        for timer in all_timers:
            timer.timeit(warmups)

    if number <= 0 and all_timers:
        # estimate number with total_time
        n = 1
        while True:
            t = sum([timer.timeit(n) for timer in all_timers])
            if t > 0.2:
                break
            n = int(n * 0.25 / t) + 1 if t else n * 2
        number = max(round(n * total_time / t / repeat), 1)

    if show_progress:
        progress_ = progress(len(all_timers) * repeat, 12)
        print(next(progress_), end='', flush=True)

    for _ in range(repeat):
        for timer in all_timers:
            t = timer.timeit(number)
            timer.times.append(t / number)
            timer.total_time += t
            if show_progress:
                print(next(progress_), end='', flush=True)

    if show_progress:
        print()

    all_results = [
        TimeitResult(timer.index, timer.stmt, repeat, number, timer.times,
                     timer.total_time)
        for timer in all_timers
    ]
    results = ComparisonResults(repeat, number, all_results)
    return results


def cmp(*timers, setup='pass', globals=None, repeat=7, number=0, total_time=1.5,
        warmups=1, show_progress=True, sort_by='mean', reverse=False,
        precision=2, percentage=None, file=None):
    """
    Convenience function to call compare function and print the results.
    See compare function and ComparisonResults.print methods for parameters.
    """
    if globals is None:
        try:
            # sys._getframe is not guaranteed to exist in all
            # implementations of Python
            globals = sys._getframe(1).f_globals
        except:
            globals = {}

    # validate the arguments of ComparisonResults.print method beforehand, to
    # avoid wasting time in case an error caused by the arguments occurs after
    # the timers have finished running
    print_args = ComparisonResults._check_print_args(
        sort_by, reverse, precision, percentage, None, None, file, None
    )

    results = compare(
        *timers,
        setup=setup,
        globals=globals,
        repeat=repeat,
        number=number,
        total_time=total_time,
        warmups=warmups,
        show_progress=show_progress
    )

    results._print(print_args)
