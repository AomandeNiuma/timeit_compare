"""
Based on the timeit library, timeit_compare can time multiple statements and
provide comparison results.

Python quick usage:
    from timeit_compare import compare

    compare(*timer_args[, setup][, globals][, repeat][, number][, time]
        [, sort_by][, reverse][, decimal])

See the function compare.

Command line usage:
    python -m timeit_compare [-s] [-r] [-n] [-t] [--sort-by] [--reverse] [-d]
        [-h] [--] [timer_args ...]

See the function main.

Note that if an error occurs during the operation of a statement, the program
will stop timing this statement, display the error type in the error cell of
the final results, and then continue to time other statements without errors.

If you actively terminate the program, all statements immediately stop timing
and then output the comparison results of the data already obtained.

To ensure a good user experience, the output terminal should use a font that
has a fixed width and supports unicode characters. Additionally, it is best not
to automatically wrap lines of text.
"""

from collections import namedtuple
from itertools import count, chain
from time import perf_counter
from timeit import Timer
from typing import Union, Sequence, Callable, Iterable

__all__ = ['TimerResult', 'Compare', 'compare']


def _percent(a, b):
    """Internal function."""
    return a / b if b else 1.0


# store the result of a timer
TimerResult = namedtuple(
    'TimerResult',
    (
        'index', 'error', 'time', 'repeat', 'number',
        'mean', 'median', 'min', 'max', 'std'
    )
)


class _Timer:
    """Internal class."""

    def __init__(self, index, stmt, setup, globals):
        self.index = index
        self.stmt = stmt
        self.timer = Timer(stmt, setup, perf_counter, globals)
        self.error = None
        self.time = []
        self.total_time = 0.0
        self.mean = self.median = self.min = self.max = self.std = None
        self._result = None

    def reset(self):
        self.error = None
        self.time.clear()
        self.total_time = 0.0
        self.mean = self.median = self.min = self.max = self.std = None
        self._result = None

    def pre_timeit(self, number):
        if self.error is None:
            try:
                time = self.timer.timeit(number)
            except Exception as e:
                self.error = type(e)
                return None, True
            else:
                return time, False
        return None, False

    def pre_interrupt(self, e):
        if self.error is None:
            self.error = type(e)
            return True
        return False

    def timeit(self, number):
        if self.error is None:
            try:
                time = self.timer.timeit(number)
            except Exception as e:
                self.error = type(e)
                return True
            else:
                self.time.append(time / number)
                self.total_time += time
        return False

    def interrupt(self, e, repeat):
        if self.error is None:
            if len(self.time) < repeat:
                self.error = type(e)
                return True
        return False

    def statistic(self):
        if self.time:
            n = len(self.time)
            mean = sum(self.time) / n
            sorted_time = sorted(self.time)
            k = n // 2
            if n & 1:
                median = sorted_time[k]
            else:
                median = (sorted_time[k] + sorted_time[k - 1]) / 2
            min_ = sorted_time[0]
            max_ = sorted_time[-1]
            if n >= 2:
                std = ((sum(i * i for i in self.time) - n * mean * mean) /
                       (n - 1)) ** 0.5
            else:
                std = None
        else:
            mean = median = min_ = max_ = std = None

        self.mean = mean
        self.median = median
        self.min = min_
        self.max = max_
        self.std = std

    def get_result(self, number):
        if self._result is None:
            self._result = TimerResult(
                self.index, self.error, self.time.copy(), len(self.time),
                number, self.mean, self.median, self.min, self.max, self.std)
        return self._result

    _null = '-'

    def get_line(self, decimal, max_mean, max_median, repeat):
        index = f'{self.index}'

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

        if self.time:
            scale = float(f"1e{f'{self.min:.0e}'.split('e', 1)[1]}")
            unit = f'{scale:.0e}s'

            dtime = decimal

            def format_time(second):
                return f'{second / scale:.{dtime}f}'

            dpercent = max(decimal - 2, 0)

            def format_percent(percent):
                d = dpercent + (
                    0 if percent >= 1.0 else
                    1 if percent >= 0.1 else
                    2
                )
                return f'{percent:#.{d}%}'

            dprocess = 5 + decimal

            def format_process(percent):
                return _process_bar(percent, dprocess)

            mean = format_time(self.mean)
            percent = _percent(self.mean, max_mean)
            mean_percent = format_percent(percent)
            mean_process = format_process(percent)

            median = format_time(self.median)
            percent = _percent(self.median, max_median)
            median_percent = format_percent(percent)
            median_process = format_process(percent)

            min_ = format_time(self.min)
            max_ = format_time(self.max)
            if len(self.time) >= 2:
                std = format_time(self.std)
            else:
                std = self._null

        else:
            unit = mean = mean_percent = mean_process = \
                median = median_percent = median_process = \
                min_ = max_ = std = self._null

        if self.error is not None:
            error = self.error.__name__
            if len(self.time) < repeat:
                error = f'{error}(r={len(self.time)})'
        else:
            error = self._null

        return (index, stmt, unit, mean, mean_percent, mean_process, median,
                median_percent, median_process, min_, max_, std, error)


class Compare:
    """Main class, used to create timers, run timers, view or print timer
    results."""

    def __init__(self) -> None:
        """Constructor."""
        self._index = count()
        self._timer = {}
        self._repeat = 0
        self._number = 0

    def reset(self) -> None:
        """Reset all timers for a rerun. All results will be deleted."""
        for timer in self._timer.values():
            timer.reset()
        self._repeat = 0
        self._number = 0

    def add_timer(
            self,
            stmt: Union[Callable, str],
            setup: Union[Callable, str] = 'pass',
            globals: dict = None
    ) -> int:
        """
        Add a timer.
        :param stmt: statement to be timed.
        :param setup: statement to be executed once initially (default 'pass').
            Execution time of this setup statement is NOT timed.
        :param globals: if specified, the code will be executed within that
            namespace (default None, inside timeit's namespace).
        :return: index of the new timer.
        """
        index = next(self._index)
        timer = _Timer(index, stmt, setup, globals)
        self._timer[index] = timer
        return index

    def del_timer(self, index: int) -> None:
        """
        Delete a timer.
        :param index: index of the timer.
        """
        del self._timer[index]

    def run(
            self,
            repeat: int = 5,
            number: int = 0,
            time: Union[float, int] = 1.0,
            include: Iterable[int] = None,
            exclude: Iterable[int] = None,
            show_process: bool = False
    ) -> None:
        """
        Run timers.
        :param repeat: how many times to repeat the timer (default 5).
        :param number: how many times to execute statement (default 0,
            estimated by time).
        :param time: approximate total running time of all statements in
            seconds (default 1.0). Ignored when number is greater than 0.
        :param include: indexes of the included timers (default None, including
            all timers).
        :param exclude: indexes of the excluded timers (default None, no timers
            are excluded).
        :param show_process: whether to show a progress bar (default False).
        """
        args = Compare._run_args(repeat, number, time, show_process)
        timers = self._select(include, exclude)
        self.reset()
        self._run(timers, *args)

    def get_result(self, index: int) -> TimerResult:
        """
        Get the result of a timer.
        :param index: index of the timer.
        :return: the result of the specified timer.
        """
        return self._timer[index].get_result(self._number)

    def get_fastest(self, sort_by: str = 'mean') -> Union[TimerResult, None]:
        """
        Get the result of the fastest timer.
        :param sort_by: the basis for sorting the results, which can be 'index',
            'mean', 'median', 'min', 'max' or 'std' (default 'mean').
        :return: the result of the specified timer.
        """
        sort_by = Compare._sort_by_args(sort_by)

        min_timer = None
        min_time = float('inf')

        for timer in self._timer.values():
            time = getattr(timer, sort_by)
            if time is not None:
                if time < min_time:
                    min_timer, min_time = timer, time

        if min_timer is not None:
            return min_timer.get_result(self._number)

    def print_results(
            self,
            sort_by: str = 'mean',
            reverse: bool = False,
            decimal: int = 2,
            include: Iterable[int] = None,
            exclude: Iterable[int] = None
    ) -> None:
        """
        Print the results of the timers in tabular form.
        :param sort_by: the basis for sorting the results, which can be 'index',
            'mean', 'median', 'min', 'max' or 'std' (default 'mean').
        :param reverse: whether to sort the results in descending order
            (default False).
        :param decimal: number of decimal places to be retained (default 2).
        :param include: indexes of the included timers (default None, including
            all timers).
        :param exclude: indexes of the excluded timers (default None, no timers
            are excluded).
        """
        args = Compare._print_results_args(sort_by, reverse, decimal)
        timers = self._select(include, exclude)
        return self._print_results(timers, *args)

    def _select(self, include=None, exclude=None):
        """Internal function."""
        if include is not None and exclude is not None:
            raise ValueError(
                'the include and exclude parameters cannot be '
                'set simultaneously')
        if include is not None:
            include = set(include)
            timers = [self._timer[index] for index in include]
        elif exclude is not None:
            exclude = set(exclude)
            include = self._timer.keys() - exclude
            timers = [self._timer[index] for index in include]
        else:
            timers = list(self._timer.values())
        return timers

    def _run(self, timers, repeat, number, time, show_process):
        """Internal function."""
        timer_num = len(timers)
        error = 0
        total_repeat = timer_num * repeat
        complete = 0

        def update_process():
            if not show_process:
                return
            process = _process_bar(_percent(complete, total_repeat), 16)
            string = (f'\r|{process}| {complete}/{total_repeat} completed, '
                      f'{error}/{timer_num} error')
            print(string, end='', flush=True)

        if show_process:
            print('timing now...')

        if number == 0:
            def estimate():
                nonlocal error
                n = 1
                while True:
                    total_time = 0.0
                    for timer in timers:
                        pre_time, turn_error = timer.pre_timeit(n)
                        if pre_time is not None:
                            total_time += pre_time
                        if turn_error:
                            error += 1
                    if error == timer_num:
                        return 0
                    if total_time > 0.2:
                        return max(round((time * (n / total_time)) / repeat), 1)
                    n <<= 1

            try:
                number = estimate()
            except (KeyboardInterrupt, SystemExit) as e:
                for timer in timers:
                    turn_error = timer.pre_interrupt(e)
                    if turn_error:
                        error += 1

        update_process()

        try:
            for _ in range(repeat):
                for timer in timers:
                    turn_error = timer.timeit(number)
                    if turn_error:
                        error += 1
                    complete += 1
                    update_process()

        except (KeyboardInterrupt, SystemExit) as e:
            for timer in timers:
                turn_error = timer.interrupt(e, repeat)
                if turn_error:
                    error += 1
            complete = total_repeat
            update_process()

        if show_process:
            print()

        for timer in timers:
            timer.statistic()

        self._repeat = repeat
        self._number = number

    def _print_results(self, timers, sort_by, reverse, decimal):
        """Internal function."""
        title = 'Comparison Results'

        header = ['Idx', 'Stmt', 'Unit', 'Mean', 'Median', 'Min', 'Max',
                  'Std', 'Err']
        if sort_by == 'index':
            i = 0
        elif sort_by == 'mean':
            i = 3
        elif sort_by == 'median':
            i = 4
        elif sort_by == 'min':
            i = 5
        elif sort_by == 'max':
            i = 6
        else:  # sort_by == 'std'
            i = 7
        header[i] = f"{header[i]} {'↓' if not reverse else '↑'}"
        header[5] = f'{header[5]} - {header.pop(6)}'

        header_cols = (1, 1, 1, 3, 3, 2, 1, 1)

        max_mean = 0.0
        max_median = 0.0
        total_time = 0.0

        for timer in timers:
            if timer.mean is not None:
                if timer.mean > max_mean:
                    max_mean = timer.mean
            if timer.median is not None:
                if timer.median > max_median:
                    max_median = timer.median
            total_time += timer.total_time

        result, result1 = [], []
        for timer in timers:
            (result if getattr(timer, sort_by) is not None else
             result1).append(timer)

        result.sort(key=lambda item: getattr(item, sort_by), reverse=reverse)
        result.extend(result1)

        body = [timer.get_line(decimal, max_mean, max_median, self._repeat)
                for timer in result]

        note = (f"{self._repeat} repetition{'s' if self._repeat != 1 else ''}, "
                f"{self._number} loop{'s' if self._number != 1 else ''} each, "
                f"total runtime {total_time:.4f}s")

        print(_table(title, header, header_cols, body, note))

    @staticmethod
    def _sort_by_args(sort_by):
        """Internal function."""
        if not isinstance(sort_by, str):
            raise TypeError(f'sort_by must be a string, not {type(sort_by)}')
        sort_by = sort_by.lower()
        if sort_by not in {'index', 'mean', 'median', 'min', 'max', 'std'}:
            raise ValueError(
                f'sort_by must be index, mean, median, min, max or std, '
                f'not {sort_by}')

        return sort_by

    @staticmethod
    def _run_args(repeat, number, time, show_process):
        """Internal function."""
        if not isinstance(repeat, int):
            raise TypeError(f'repeat must be a integer, not {type(repeat)}')
        if repeat < 1:
            repeat = 1

        if not isinstance(number, int):
            raise TypeError(f'number must be a integer, not {type(number)}')
        if number < 0:
            number = 0

        if not isinstance(time, (float, int)):
            raise TypeError(f'time must be a real number, not {type(time)}')
        if time < 0.0:
            time = 0.0

        show_process = bool(show_process)

        return repeat, number, time, show_process

    @staticmethod
    def _print_results_args(sort_by, reverse, decimal):
        """Internal function."""
        sort_by = Compare._sort_by_args(sort_by)

        reverse = bool(reverse)

        if not isinstance(decimal, int):
            raise TypeError(f'decimal must be a integer, not {type(decimal)}')
        if decimal < 0:
            decimal = 0
        elif decimal > 8:
            decimal = 8

        return sort_by, reverse, decimal


def compare(
        *timer_args: Union[Sequence, Callable, str],
        setup: Union[Callable, str] = 'pass',
        globals: dict = None,
        repeat: int = 5,
        number: int = 0,
        time: Union[float, int] = 1.0,
        sort_by: str = 'mean',
        reverse: bool = False,
        decimal: int = 2
) -> None:
    """
    Convenience function to create Compare object, call add_timer, run and
    print_results methods.

    :param timer_args: a sequence (statement, setup, globals) or a single
        statement for Compare.add_timer method.
    :param setup: default setup for positional parameters with no or None setup
        given (default: same as Compare.add_timer).
    :param globals: default globals for positional parameters with no or None
        globals given (default: same as Compare.add_timer).

    See add_timer, run, and print_results methods of the class Compare.
    """
    run_args = Compare._run_args(repeat, number, time, True)
    print_results_args = Compare._print_results_args(sort_by, reverse, decimal)
    cmp = Compare()
    for args in timer_args:
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
    timers = cmp._select()
    cmp._run(timers, *run_args)
    cmp._print_results(timers, *print_results_args)


_BLOCK = ' ▏▎▍▌▋▊▉█'


def _process_bar(process, length):
    """Internal function."""
    if process <= 0.0:
        string = ' ' * length

    elif process >= 1.0:
        string = _BLOCK[-1] * length

    else:
        d = 1.0 / length
        q = process // d
        block1 = _BLOCK[-1] * int(q)

        r = process % d
        d2 = d / 8
        i = (r + d2 / 2) // d2
        block2 = _BLOCK[int(i)]

        block3 = ' ' * (length - len(block1) - len(block2))

        string = f'{block1}{block2}{block3}'

    return string


_TABLE_NUMBER = count(1)


def _table(title, header, header_cols, body, note):
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
                q, r = bw // col, bw % col
                for j in range(i, i + col):
                    body_width[j] += q
                for j in range(i, i + r):
                    body_width[j] += 1
        if hw < bw:
            hw = bw
        header_width.append(hw)
        i += col

    total_width = sum(header_width) + len(header_width) + 1
    other_width = max(len(title), len(note))
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

    lines = [title_line, top_border, header_line, split_border]
    lines.extend([body_line] * len(body))
    lines.append(bottom_border)
    lines.append(note_line)
    template = '\n'.join(lines)

    return template.format(
        title,
        *header,
        *chain.from_iterable(body),
        note
    )


def main() -> None:
    """Usage:
  python -m timeit_compare [-s] [-r] [-n] [-t] [--sort-by] [--reverse] [-d] [-h]
    [--] [timer_args ...]

Options:
  -s, --setup       default setup for positional parameters with no setup given
                    (default 'pass').
  -r, --repeat      how many times to repeat the timer (default 5).
  -n, --number      how many times to execute statement (default 0, estimated
                    by time).
  -t, --time        approximate total running time of all statements in seconds
                    (default 1.0). Ignored when number is greater than 0.
  --sort-by         the basis for sorting the results, which can be 'index',
                    'mean', 'median', 'min', 'max' or 'std' (default 'mean').
  --reverse         whether to sort the results in descending order (default
                    False).
  -d, --decimal     number of decimal places to be retained (default 2).
  -h, --help        print this usage message and exit.
  --                separate options from statement, use when statement starts
                    with '-'.
  timer_args        statement to be timed (statement) and statement to be
                    executed once initially (setup, default -s).
                    Statement and setup are given in a single argument,
                    separated by ';;', multi-line statement and setup can be
                    given by separating lines with ';'. Execution time of the
                    setup statement is NOT timed."""
    import sys
    args = sys.argv[1:]

    import getopt
    try:
        opts, args = getopt.getopt(
            args, 's:r:n:t:d:h',
            ['setup=', 'repeat=', 'number=', 'time=', 'sort-by=',
             'reverse', 'decimal=', 'help'])
    except getopt.error as e:
        error = str(e)
    else:
        error = None
    if error is not None:
        raise getopt.error(f'{error}\nuse -h/--help for command line help')

    timer_args = [
        [j.replace(';', '\n') for j in i.split(';;', 1)]
        for i in args
    ]
    setup = []
    globals = None
    repeat = 5
    number = 0
    time = 1.0
    sort_by = 'mean'
    reverse = False
    decimal = 2
    for k, v in opts:
        if k in ('-s', '--setup'):
            setup.append(v.replace(';', '\n'))
        elif k in ('-r', '--repeat'):
            repeat = int(v)
        elif k in ('-n', '--number'):
            number = int(v)
        elif k in ('-t', '--time'):
            time = float(v)
        elif k == '--sort-by':
            sort_by = v
        elif k == '--reverse':
            reverse = True
        elif k in ('-d', '--decimal'):
            decimal = int(v)
        elif k in ('-h', '--help'):
            print(main.__doc__)
            return
    setup = '\n'.join(setup) if setup else 'pass'

    import os
    sys.path.insert(0, os.curdir)

    compare(
        *timer_args,
        setup=setup,
        globals=globals,
        repeat=repeat,
        number=number,
        time=time,
        sort_by=sort_by,
        reverse=reverse,
        decimal=decimal
    )


if __name__ == '__main__':
    main()
