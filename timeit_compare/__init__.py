"""
Based on the timeit library, timeit_compare can conveniently measure execution
times of multiple statements and provide some basic descriptive statistics to
compare the results.

Python quick usage:
    from timeit_compare import compare

    compare(*add_timers[, setup][, globals][, add_stats][, repeat][, number]
        [, time][, show_progress][, sort_by][, reverse][, stats][, percentage]
        [, precision])

See the function compare.

Command line usage:
    python -m timeit_compare [-h] [-v] [-a ADD_TIMERS [ADD_TIMERS ...]]
        [-s SETUP [SETUP ...]] [-r REPEAT] [-n NUMBER] [-t TIME] [--no-progress]
        [--sort-by {mean,median,min,max,std}] [--no-sort] [--reverse]
        [--stats [{mean,median,min,max,std} ...]]
        [--percentage [{mean,median,min,max,std} ...]] [-p PRECISION]

Run 'python -m timeit_compare -h' for command line help.
"""

# python >= 3.6

import itertools
import statistics
import sys
import time
from collections import namedtuple, OrderedDict
from keyword import iskeyword
from timeit import Timer
from typing import Sequence

if sys.version_info >= (3, 7):
    OrderedDict = dict

__version__ = '1.3.0'

__all__ = ['TimerResult', 'Compare', 'compare']

# store the result of a timer
TimerResult = namedtuple('TimerResult', (
    'id', 'repeat', 'stats', 'time', 'number'))

_DEFAULT_STATS = OrderedDict(
    mean=statistics.fmean if sys.version_info >= (3, 8) else statistics.mean,
    median=statistics.median,
    min=min,
    max=max,
    std=statistics.stdev
)


def _stat_call(func, time):
    """Internal function."""
    try:
        value = func(time)
        if isinstance(value, (float, int)):
            return value
    except:
        pass


class _Timer(Timer):
    """Internal class."""

    def __init__(self, stmt, setup, globals):
        super().__init__(stmt, setup, time.perf_counter, globals)
        self.id = -1
        self.stmt = stmt
        self.time = ()
        self.total_time = 0.0
        self.stats = {}
        self._result = None

    repeat = property(lambda self: len(self.time))

    def add_stat(self, stat, func):
        self.stats[stat] = _stat_call(func, self.time)
        self._result = None

    def del_stat(self, stat):
        del self.stats[stat]
        self._result = None

    if sys.version_info >= (3, 11):
        def timeit(self, number):
            try:
                return super().timeit(number)
            except Exception as e:
                e.add_note(f'(timer id: {self.id})')
                raise

    def get_result(self, number, stats_namedtuple):
        if self._result is None:
            self._result = TimerResult(
                id=self.id,
                repeat=self.repeat,
                stats=stats_namedtuple(**self.stats),
                time=self.time,
                number=number)
        return self._result

    def get_line(self, stats, max_value, precision):
        line = []

        id = f'{self.id}'
        line.append(id)

        if isinstance(self.stmt, str):
            stmt = repr(self.stmt)[1:-1]
        elif callable(self.stmt):
            if hasattr(self.stmt, '__name__'):
                stmt = f'{self.stmt.__name__}()'
            else:
                stmt = self._null
        else:
            stmt = self._null
        if len(stmt) > 25:
            stmt = f'{stmt[:24]}…'
        line.append(stmt)

        repeat = f'{self.repeat}'
        line.append(repeat)

        p_time = precision
        p_percentage = max(precision - 2, 0)
        p_progress = 5 + precision

        for stat in stats:
            value = self.stats[stat]

            if value is not None:
                key_time = self.format_time(value, p_time)
            else:
                key_time = self._null
            line.append(key_time)

            if stat in max_value:
                if value is not None:
                    percent = value / max_value[stat] \
                        if max_value[stat] else 1.0
                    key_percent = [
                        self.format_percentage(percent, p_percentage),
                        self.format_progress(percent, p_progress)]
                else:
                    key_percent = [self._null, self._null]
                line.extend(key_percent)

        return line

    _null = '-'

    @staticmethod
    def format_time(second, p):
        s = f'{second:#.{p}g}'
        if 'e' in s:
            # 1e+05 -> 1e+5
            a, b = s.split('e', 1)
            s = f'{a}e{int(b):+}'
        return s

    @staticmethod
    def format_percentage(percent, p):
        k = 1.0 - 5 * 0.1 ** (p + 4)
        d = p + (
            0 if percent >= k else
            1 if percent >= 0.1 * k else
            2
        )
        return f'{percent:#.{d}%}'

    @staticmethod
    def format_progress(percent, p):
        return _progress_bar(percent, p)


class Compare:
    """Main class, used to create timers, create statistics, run timers, and get
    or print results."""

    def __init__(self):
        """Constructor."""
        self._timer_id = itertools.count()
        self._timer = OrderedDict()
        self._stats = _DEFAULT_STATS.copy()
        self._number = 0
        self._stats_namedtuple = None

    def add_timer(self, stmt, setup='pass', globals=None):
        """
        Add a new timer.
        :param stmt: statement to be timed.
        :param setup: statement to be executed once initially (default: 'pass').
            Execution time of this setup statement is NOT timed.
        :param globals: if specified, the code will be executed within that
            namespace (default: {}).
        :return: an identifier for the new timer.
        """
        if globals is None:
            globals = {}
        timer = _Timer(stmt, setup, globals)
        for stat, func in self._stats.items():
            timer.add_stat(stat, func)
        id = next(self._timer_id)
        timer.id = id
        self._timer[id] = timer
        return id

    def del_timer(self, id):
        """
        Delete a timer.
        :param id: timer id.
        """
        del self._timer[id]

    def add_stat(self, stat, func):
        """
        Add a new statistic.
        :param stat: name of the new statistic.
        :param func: a function to calculate the new statistic. This function
            should allow receiving a tuple composed of floating point time and
            return a real number or None.
        """
        stat = self._check_stat(stat)

        if not callable(func):
            raise TypeError(f'func must be a callable, not '
                            f'{type(func).__name__!r}')

        self._stats[stat] = func
        self._stats_namedtuple = None
        for timer in self._timer.values():
            timer.add_stat(stat, func)

    def _check_stat(self, stat, message='stat'):
        """Internal function."""
        if type(stat) is not str:
            raise TypeError(f'{message} must be a string, not '
                            f'{type(stat).__name__!r}')
        if not stat.isidentifier():
            raise ValueError(f'{message} must be a valid identifier, not '
                             f'{stat!r}')
        if iskeyword(stat):
            raise ValueError(f'{message} cannot be a keyword: {stat!r}')
        if stat.startswith('_'):
            raise ValueError(f'{message} cannot start with an underscore: '
                             f'{stat!r}')
        return stat.lower()

    def del_stat(self, stat):
        """
        Delete a statistic.
        :param stat: name of the statistic.
        """
        stat = self._check_stat_select(stat)

        del self._stats[stat]
        self._stats_namedtuple = None
        for timer in self._timer.values():
            timer.del_stat(stat)

    def _check_stat_select(self, stat, message='stat'):
        """Internal function."""
        stat = self._check_stat(stat, message)
        if stat not in self._stats:
            raise ValueError(
                f"stat {stat!r} is not in the optional statistics: "
                f"{{{', '.join(map(repr, self._stats))}}}.")
        return stat

    def run(self, repeat=5, number=0, time=1.0, show_progress=False):
        """
        Run timers.
        :param repeat: how many times to repeat the timer (default: 5).
        :param number: how many times to execute statement (default: estimated
            by time).
        :param time: if specified and no number greater than 0 is specified, it
            will be used to estimate a number so that the total execution time
            (in seconds) of all statements is approximately equal to this value
            (default: 1.0).
        :param show_progress: whether to show a progress bar (default: False).
        """
        if not isinstance(repeat, int):
            raise TypeError(f'repeat must be a integer, not '
                            f'{type(repeat).__name__!r}')
        if repeat < 1:
            repeat = 1

        if not isinstance(number, int):
            raise TypeError(f'number must be a integer, not '
                            f'{type(number).__name__!r}')

        if not isinstance(time, (float, int)):
            raise TypeError(f'time must be a real number, not '
                            f'{type(time).__name__!r}')
        if time < 0.0:
            time = 0.0

        show_progress = bool(show_progress)

        if not self._timer:
            return

        if show_progress:
            print('timing now...')

        # Temporarily store the results and update them to the instance
        # properties after all processing is completed and no errors occur
        new = {
            timer: {
                'time': [],
                'total_time': 0.0,
                'stats': {},
                '_results': None
            }
            for timer in self._timer.values()
        }

        catch_interrupt = hasattr(self, '_catch_interrupt')

        try:
            if number <= 0:
                n = 1
                while True:
                    t = 0.0
                    for timer in new:
                        t += timer.timeit(n)
                    if t > 0.2:
                        number = max(round(n * time / t / repeat), 1)
                        break
                    n = int(n * 0.25 / t) + 1 if t else n * 2

            if show_progress:
                progress = self._run_progress(len(new) * repeat)
            else:
                progress = itertools.repeat(None)

            next(progress)
            for _ in range(repeat):
                for timer, result in new.items():
                    t = timer.timeit(number)
                    result['time'].append(t / number)
                    result['total_time'] += t
                    next(progress)

        except KeyboardInterrupt as e:
            if not catch_interrupt:
                raise
            self._catch_interrupt = e

        if show_progress:
            print()

        for result in new.values():
            result['time'] = tuple(result['time'])
            for stat, func in self._stats.items():
                result['stats'][stat] = _stat_call(func, result['time'])

        # update new results
        for timer, result in new.items():
            timer.__dict__.update(result)
        self._number = number

    @staticmethod
    def _run_progress(task_num):
        for i in range(task_num + 1):
            progress = (f'\r|{_progress_bar(i / task_num, 12)}| '
                        f'{i}/{task_num} completed')
            print(progress, end='', flush=True)
            yield

    def get_result(self, id):
        """
        Get the result of a timer.
        :param id: timer id.
        :return: the result of the specified timer.
        """
        if self._stats_namedtuple is None:
            self._stats_namedtuple = namedtuple('Stats', self._stats)
        return self._timer[id].get_result(
            self._number, self._stats_namedtuple)

    def get_min(self, stat='mean'):
        """
        Get the result of the timer with the minimum statistic.
        :param stat: search by this statistic (default: 'mean').
        :return: the result of the specified timer.
        """
        stat = self._check_stat_select(stat)

        min_id = None
        min_value = float('inf')

        for id, timer in self._timer.items():
            value = timer.stats[stat]
            if value is not None:
                if value < min_value:
                    min_id, min_value = id, value

        if min_id is not None:
            return self.get_result(min_id)

    def get_max(self, stat='mean'):
        """
        Get the result of the timer with the maximum statistic.
        :param stat: search by this statistic (default: 'mean').
        :return: the result of the specified timer.
        """
        stat = self._check_stat_select(stat)

        max_id = None
        max_value = float('-inf')

        for id, timer in self._timer.items():
            value = timer.stats[stat]
            if value is not None:
                if value > max_value:
                    max_id, max_value = id, value

        if max_id is not None:
            return self.get_result(max_id)

    def print_results(self, include=None, exclude=None, sort_by='mean',
                      reverse=False, stats=None, percentage=None, precision=2):
        """
        Print the results of the timers in tabular form.
        :param include: ids of the included timers (default: including all
            timers).
        :param exclude: ids of the excluded timers (default: no timers
            excluded).
        :param sort_by: statistic for sorting the results (default: 'mean'). If
            None is specified, no sorting will be performed.
        :param reverse: whether to sort the results in descending order
            (default: False).
        :param stats: statistics in the column headers of the table (default:
            all statistics in default order).
        :param percentage: statistics showing percentage (default: same as
            sort_by).
        :param precision: digits precision of the results (default: 2).
        """
        args = self._print_results_args(
            include, exclude, sort_by, reverse, stats, percentage, precision)
        return self._print_results(*args)

    def _print_results_args(self, include, exclude, sort_by, reverse, stats,
                            percentage, precision):
        """Internal function."""
        if include is not None and exclude is not None:
            raise ValueError('include and exclude cannot be set simultaneously')
        if include is not None:
            include = set(include)
            timers = [self._timer[i] for i in include]
        elif exclude is not None:
            exclude = set(exclude)
            timers = [timer for i, timer in self._timer.items()
                      if i not in exclude]
        else:
            timers = list(self._timer.values())

        if sort_by is not None:
            sort_by = self._check_stat_select(sort_by, 'sort_by')

        reverse = bool(reverse)

        if stats is None:
            stats = list(self._stats)
        else:
            if isinstance(stats, str):
                stats = stats.replace(',', ' ').split()
            stats = [self._check_stat_select(stat) for stat in stats]

        if percentage is None:
            percentage = sort_by
        if percentage is None:
            percentage = []
        elif isinstance(percentage, str):
            percentage = percentage.replace(',', ' ').split()
        percentage = {self._check_stat_select(stat, 'item in percentage')
                      for stat in percentage}
        percentage &= set(stats)

        if not isinstance(precision, int):
            raise TypeError(f'precision must be a integer, not '
                            f'{type(precision).__name__!r}')
        if precision < 1:
            precision = 1
        elif precision > 8:
            precision = 8

        return timers, sort_by, reverse, stats, percentage, precision

    def _print_results(self, timers, sort_by, reverse, stats, percentage,
                       precision):
        """Internal function."""
        title = 'Comparison Results (unit: s)'

        header = ['Id', 'Stmt', 'Rpt', *(stat.title() for stat in stats)]
        if sort_by is not None:
            for i, stat in enumerate(stats, 3):
                if stat == sort_by:
                    header[i] = f"{header[i]} {'↓' if not reverse else '↑'}"

            timers_sort, timers_none = [], []
            for timer in timers:
                (timers_sort if timer.stats[sort_by] is not None else
                 timers_none).append(timer)
            timers_sort.sort(key=lambda item: item.stats[sort_by],
                             reverse=reverse)
            timers = timers_sort + timers_none

        header_cols = [1] * len(header)
        for i, stat in enumerate(stats, 3):
            if stat in percentage:
                header_cols[i] = 3

        max_value = dict.fromkeys(percentage, 0.0)
        for timer in timers:
            for stat in percentage:
                value = timer.stats[stat]
                if value is not None:
                    if value > max_value[stat]:
                        max_value[stat] = value

        body = [timer.get_line(stats, max_value, precision) for timer in timers]

        total_time = sum(timer.total_time for timer in timers)
        notes = [
            f"{self._number} execution{'s' if self._number != 1 else ''} for "
            f"each statement per repetition",
            f"total execution time {total_time:.4f}s"
        ]

        print(_table(title, header, header_cols, body, notes))


def compare(*add_timers, setup='pass', globals=None, add_stats=(), repeat=5,
            number=0, time=1.0, show_progress=True, sort_by='mean',
            reverse=False, stats=None, percentage=None, precision=2):
    """
    Convenience function to create Compare object, call add_timer, add_stat, run
    and print_results methods.

    :param add_timers: (statement, setup, globals) or a single statement for
        Compare.add_timer method.
    :param setup: the global default value for setup in add_timers (default:
        same as Compare.add_timer).
    :param globals: the global default value for globals in add_timers (default:
        same as Compare.add_timer).
    See add_timer, add_stat, run, and print_results methods of the class Compare
    for other parameters.

    If the program is interrupted by Ctrl+C, the results will still be printed.
    """
    cmp = Compare()

    for args in add_timers:
        if isinstance(args, Sequence) and not isinstance(args, str):
            args = list(args)
            if len(args) < 3:
                args.extend([None] * (3 - len(args)))
            if args[1] is None:
                args[1] = setup
            if args[2] is None:
                args[2] = globals
        else:
            args = args, setup, globals
        cmp.add_timer(*args)

    for stat, func in add_stats:
        cmp.add_stat(stat, func)

    # Validate the arguments of print_results method beforehand to avoid wasting
    # time in case an error caused by the arguments occurs after the timers have
    # finished running
    print_results_args = cmp._print_results_args(
        None, None, sort_by, reverse, stats, percentage, precision)

    cmp._catch_interrupt = None
    cmp.run(repeat, number, time, show_progress)
    interrupt = cmp._catch_interrupt

    cmp._print_results(*print_results_args)

    if interrupt is not None:
        raise interrupt


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


_TABLE_NUMBER = itertools.count(1)


def _table(title, header, header_cols, body, notes):
    """Internal function."""
    title = f'Table {next(_TABLE_NUMBER)}. {title}'

    body_width = [2] * sum(header_cols)
    for i, item in enumerate(zip(*body)):
        body_width[i] += max(map(len, item))

    header_width = []
    i = 0
    for s, col in zip(header, header_cols):
        hw = len(s) + 2
        if col == 1:
            bw = body_width[i]
            if hw > bw:
                body_width[i] = hw
        else:
            bw = sum(body_width[i: i + col]) + col - 1
            if hw > bw:
                bw = hw - bw
                q, r = divmod(bw, col)
                for j in range(i, i + col):
                    body_width[j] += q
                for j in range(i, i + r):
                    body_width[j] += 1
        if hw < bw:
            hw = bw
        header_width.append(hw)
        i += col

    total_width = sum(header_width) + len(header_width) + 1
    other_width = max(len(title), *map(len, notes))
    if other_width > total_width:
        bw = other_width - total_width
        dl = ' ' * (bw // 2)
        dr = ' ' * (bw - bw // 2)
        total_width = other_width
    else:
        dl = dr = ''

    title_line = f'{{:^{total_width}}}'
    header_line = f"{dl}│{'│'.join(f'{{:^{hw}}}' for hw in header_width)}│{dr}"
    body_line = f"{dl}│{'│'.join(f'{{:^{bw}}}' for bw in body_width)}│{dr}"
    note_line = f'{{:<{total_width}}}'

    top_border = f"{dl}╭{'┬'.join('─' * hw for hw in header_width)}╮{dr}"
    bottom_border = f"{dl}╰{'┴'.join('─' * bw for bw in body_width)}╯{dr}"
    split_border = []
    bw = iter(body_width)
    for col in header_cols:
        if col == 1:
            border = '─' * next(bw)
        else:
            border = '┬'.join('─' * next(bw) for _ in range(col))
        split_border.append(border)
    split_border = f"{dl}├{'┼'.join(split_border)}┤{dr}"

    template = '\n'.join(
        (
            title_line,
            top_border,
            header_line,
            split_border,
            *[body_line] * len(body),
            bottom_border,
            *[note_line] * len(notes)
        )
    )

    return template.format(
        title,
        *header,
        *itertools.chain.from_iterable(body),
        *notes
    )
