"""
Conveniently measure and compare the execution times of multiple statements.

Python quick usage:
    from timeit_compare import cmp

    cmp(*timers[, setup][, globals][, repeat][, number][, total_time]
        [, show_progress][, sort_by][, reverse][, precision][, percentage])

See the function cmp.

Command line usage:
    python -m timeit_compare [-h] [-v] [- STMT [STMT ...]] [-s [SETUP ...]]
        [-r REPEAT] [-n NUMBER] [-t TOTAL_TIME] [--no-progress]
        [--sort-by {mean,median,min,max,stdev}] [--no-sort] [--reverse]
        [-p PRECISION] [--percentage [{mean,median,min,max,stdev} ...]]

Run 'python -m timeit_compare -h' for command line help.
"""

import itertools
import sys
import time
from timeit import Timer

# python >= 3.6

__version__ = '1.4.1'

__all__ = ['TimeitResult', 'ComparisonResults', 'compare', 'cmp']

_stats = ('mean', 'median', 'min', 'max', 'stdev')


class TimeitResult:
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

    def print(self, precision=2):
        """
        Print the result in tabular form.
        :param precision: digits precision of the result, ranging from 1 to 8
            (default: 2).
        """
        if not isinstance(precision, int):
            raise TypeError(f'precision must be a integer, not '
                            f'{type(precision).__name__!r}')
        if precision < 1:
            precision = 1
        elif precision > 8:
            precision = 8
        print(self._table(precision))

    def _table(self, precision):
        """Internal function."""
        title = 'Timeit Result (unit: s)'
        header = ['Idx', *(stat.title() for stat in _stats), 'Stmt']
        header_cols = [1] * len(header)
        body = self._get_line(precision, {})
        body_aligns = ['c'] * sum(header_cols)
        body_aligns[-1] = 'l'
        note = (f"{self.repeat} run{'s' if self.repeat != 1 else ''}, "
                f"{self.number} loop{'s' if self.number != 1 else ''} each, "
                f"total time {self.total_time:#.4g}s")
        if self.unreliable:
            note += (
                '\n*: Marked results are likely unreliable as the worst '
                'time was more than four times slower than the best time.')
        table = _table(title, header, header_cols, body, body_aligns, note)
        if self.unreliable:
            # mark unreliable tips in red
            table = table.splitlines(keepends=True)
            i = 3
            while table[i][0] != '─':
                i += 1
            i += 1
            table[i] = table[i].replace('*', '\x1b[31m*\x1b[0m', 1)
            i = -1
            while table[i][0] != '*':
                i -= 1
            table[i] = '\x1b[31m' + table[i]
            table[-1] += '\x1b[0m'
            table = ''.join(table)
        return table

    _null = '-'

    def _get_line(self, precision, max_value):
        """Internal function."""
        line = []

        index = f'{self.index}'
        if self.unreliable:
            index += '*'
        line.append(index)

        p_percentage = max(precision - 2, 0)
        k = 1.0 - 5 * 0.1 ** (p_percentage + 4)
        for stat in _stats:
            value = getattr(self, stat)

            if value is not None:
                key_time = f'{value:#.{precision}g}'
                if 'e' in key_time:
                    # '1e+05' -> '1e+5', reduce the width of the table
                    a, b = key_time.split('e', 1)
                    key_time = f'{a}e{int(b):+}'
                line.append(key_time)

                if stat in max_value:
                    percent = value / max_value[stat] \
                        if max_value[stat] else 1.0

                    # make the widths of a column of percentage strings the same
                    # so that it looks neat
                    p = p_percentage + (
                        0 if percent >= k else
                        1 if percent >= 0.1 * k else
                        2
                    )
                    key_percent = f'{percent:#.{p}%}'
                    line.append(key_percent)

                    key_progress = _progress_bar(percent, precision + 5)
                    line.append(key_progress)

            else:
                line.append(self._null)

                if stat in max_value:
                    line.append(self._null)
                    line.append(self._null)

        if isinstance(self.stmt, str):
            stmts = self.stmt.strip('\n').splitlines()
            if not stmts:
                lines = [line + [self._null]]
            else:
                iter_stmts = iter(stmts)
                lines = [line + [next(iter_stmts)]]
                for stmt in iter_stmts:
                    lines.append([self._null] * len(line) + [stmt])
        elif callable(self.stmt) and hasattr(self.stmt, '__name__'):
            lines = [line + [self.stmt.__name__ + '()']]
        else:
            lines = [line + [self._null]]

        return lines


class ComparisonResults:
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
              include=None, exclude=None):
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
        """
        args = self._check_print_args(
            sort_by, reverse, precision, percentage, include, exclude)
        print(self._table(*args))

    @staticmethod
    def _check_print_args(sort_by, reverse, precision, percentage, include,
                          exclude):
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
        elif exclude is not None:
            exclude = set(exclude)

        return sort_by, reverse, precision, percentage, include, exclude

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

    def _table(self, sort_by, reverse, precision, percentage, include,
               exclude):
        """Internal function."""
        title = 'Comparison Results (unit: s)'

        if include is not None:
            results = [self._results[i] for i in include]
        elif exclude is not None:
            results = [result for i, result in enumerate(self._results)
                       if i not in exclude]
        else:
            results = self._results

        header = ['Idx', *(stat.title() for stat in _stats), 'Stmt']
        if sort_by is not None:
            i = 1 + _stats.index(sort_by)
            header[i] += ' ↓' if not reverse else ' ↑'

            results_sort, results_none = [], []
            for result in results:
                (results_sort if getattr(result, sort_by) is not None else
                 results_none).append(result)
            results_sort.sort(key=lambda result: getattr(result, sort_by),
                              reverse=reverse)
            results = results_sort + results_none

        header_cols = [1] * len(header)
        for i, stat in enumerate(_stats, 1):
            if stat in percentage:
                header_cols[i] = 3

        max_value = dict.fromkeys(percentage, 0.0)
        for result in results:
            for stat in percentage:
                value = getattr(result, stat)
                if value is not None and value > max_value[stat]:
                    max_value[stat] = value

        body = []
        for result in results:
            body.extend(result._get_line(precision, max_value))

        body_aligns = ['c'] * sum(header_cols)
        body_aligns[-1] = 'l'

        note = (f"{self.repeat} run{'s' if self.repeat != 1 else ''}, "
                f"{self.number} loop{'s' if self.number != 1 else ''} each, "
                f"total time {self.total_time:#.4g}s")
        if self.unreliable:
            note += (
                '\n*: Marked results are likely unreliable as the worst '
                'time was more than four times slower than the best time.')

        table = _table(title, header, header_cols, body, body_aligns, note)
        if self.unreliable:
            # mark unreliable tips in red
            table = table.splitlines(keepends=True)
            i = 3
            while table[i][0] != '─':
                i += 1
            i += 1
            while table[i][0] != '─':
                line = table[i]
                if line.split(None, 1)[0][-1] == '*':
                    table[i] = line.replace('*', '\x1b[31m*\x1b[0m', 1)
                i += 1
            i = -1
            while table[i][0] != '*':
                i -= 1
            table[i] = '\x1b[31m' + table[i]
            table[-1] += '\x1b[0m'
            table = ''.join(table)

        return table


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
            total_time=1.5, show_progress=False):
    """
    Measure the execution times of multiple statements and return comparison
    results.
    :param timers: (stmt, setup, globals) or a single stmt for timeit.Timer.
    :param setup: default setup statement for timeit.Timer (default: 'pass').
    :param globals: default globals for timeit.Timer (default: global namespace
        seen by the caller's frame, if this is not possible, it defaults to {},
        specify globals=globals() or setup instead).
    :param repeat: how many times to repeat the timer (default: 7).
    :param number: how many times to execute statement (default: estimated by
        total_time).
    :param total_time: if specified and no number greater than 0 is specified,
        it will be used to estimate a number so that the total execution time
        (in seconds) of all statements is approximately equal to this value
        (default: 1.5).
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

    if number <= 0 and all_timers:
        # estimate number with total_time
        n = 1
        while True:
            t = sum([timer.timeit(n) for timer in all_timers])
            if t > 0.2:
                number = max(round(n * total_time / t / repeat), 1)
                break
            n = int(n * 0.25 / t) + 1 if t else n * 2

    if show_progress:
        def _progress(task_num):
            for i in range(task_num + 1):
                percent = i / task_num if task_num else 1.0
                progress = (f'\r|{_progress_bar(percent, 12)}| '
                            f'{i}/{task_num} completed')
                print(progress, end='', flush=True)
                yield

        progress = _progress(len(all_timers) * repeat)
    else:
        progress = itertools.repeat(None)

    next(progress)
    for _ in range(repeat):
        for timer in all_timers:
            t = timer.timeit(number)
            timer.times.append(t / number)
            timer.total_time += t
            next(progress)

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
        show_progress=True, sort_by='mean', reverse=False, precision=2,
        percentage=None):
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
        sort_by, reverse, precision, percentage, include=None, exclude=None
    )

    results = compare(
        *timers,
        setup=setup,
        globals=globals,
        repeat=repeat,
        number=number,
        total_time=total_time,
        show_progress=show_progress
    )

    print(results._table(*print_args))


_BLOCK = ' ▏▎▍▌▋▊▉█'


def _progress_bar(progress, length):
    """Internal function."""
    if progress <= 0.0:
        string = ' ' * length

    elif progress >= 1.0:
        string = _BLOCK[-1] * length

    else:
        d = 1.0 / length
        q, r = divmod(progress, d)
        full = _BLOCK[-1] * int(q)
        d2 = d / 8
        i = (r + d2 / 2) // d2
        half_full = _BLOCK[int(i)]
        empty = ' ' * (length - len(full) - len(half_full))
        string = f'{full}{half_full}{empty}'

    return string


def _wrap(text, width):
    """Internal function."""
    result = []
    for line in text.splitlines():
        line = line.rstrip(' ')
        if not line:
            result.append('')
            continue
        while line:
            if len(line) <= width:
                result.append(line)
                break
            for split in range(width, -1, -1):
                if line[split] == ' ':
                    break
            else:
                split = width
            result.append(line[:split].rstrip(' '))
            line = line[split:].lstrip(' ')
    return result


def _table(title, header, header_cols, body, body_aligns, note):
    """Internal function."""
    title = 'Table. ' + title

    if body:
        body_width = [max(map(len, col)) for col in zip(*body)]

        header_width = []
        i = 0
        for h, hc in zip(header, header_cols):
            hw = len(h)
            if hc == 1:
                bw = body_width[i]
                if hw > bw:
                    body_width[i] = hw
            else:
                bw = sum(body_width[i: i + hc]) + 3 * (hc - 1)
                if hw > bw:
                    dw = hw - bw
                    q, r = divmod(dw, hc)
                    for j in range(i, i + hc):
                        body_width[j] += q
                    for j in range(i, i + r):
                        body_width[j] += 1
            if hw < bw:
                hw = bw
            header_width.append(hw)
            i += hc
    else:
        body_width = []
        header_width = [len(h) for h in header]

    table_width = sum(header_width) + 3 * (len(header_width) - 1) + 2 * 2
    title = _wrap(title, table_width)
    note = _wrap(note, table_width)

    title_line = f'{{:^{table_width}}}'
    header_line = f"  {'   '.join(f'{{:^{hw}}}' for hw in header_width)}  "
    aligns = {'l': '<', 'r': '>', 'c': '^'}
    body_line = '   '.join(
        f'{{:{aligns[ba]}{bw}}}' for ba, bw in zip(body_aligns, body_width))
    body_line = f'  {body_line}  '
    note_line = f'{{:<{table_width}}}'
    border = '─' * table_width

    template = '\n'.join(
        (
            *(title_line,) * len(title),
            border,
            header_line,
            border,
            *(body_line,) * len(body),
            border,
            *(note_line,) * len(note)
        )
    )

    return template.format(*itertools.chain(title, header, *body, note))
