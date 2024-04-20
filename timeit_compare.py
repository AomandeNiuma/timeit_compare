"""
A method based on timeit that can help you to call timeit.timeit for several
statements and provide comparison results.

In-Script usage:
    from timeit_compare import compare

    compare(*stmts[, setup][, globals][, number][, repeat][, sort_by]
        [, reverse][, decimal])

See parameters in the function compare.

Command line usage:
    python -m timeit_compare.py [-s] [-n] [-r] [--sort-by] [--reverse] [-d]
        [-h] [--] [statements]

See options in the function main.

Note that if an error occurs during the operation of a statement, the
program will stop timing this statement, display the error type in the
error cell of the final results, and then continue to time other statements
without errors.

If you actively terminate the program, all statements immediately stop
timing and output the results obtained before the program terminates.

To ensure a good user experience, the output terminal should utilize a font
that has a fixed width and supports unicode characters. Additionally, it
should refrain from automatically wrapping text to a new line when it
becomes excessively long. The default output terminal in PyCharm is a good
example.
"""

from time import perf_counter
from timeit import Timer
from typing import Sequence, Callable, Union

__all__ = ['compare']


class _TimerTask:
    """Internal class."""

    def __init__(self, index, stmt, setup, globals):
        self.index = index
        self.stmt = stmt

        try:
            timer = Timer(stmt, setup, perf_counter, globals)
        except Exception as e:
            timer = None
            error = type(e)
        else:
            error = None
        self.timer = timer
        self.error = error

        self.time = []
        self.repeat = 0

    def autorange_timeit(self, number):
        if self.error is None:
            try:
                time = self.timer.timeit(number)
            except Exception as e:
                self.error = type(e)
            else:
                return time

    def autorange_interrupt(self, e):
        if self.error is None:
            self.error = type(e)

    def timeit(self, number):
        if self.error is None:
            try:
                time = self.timer.timeit(number)
            except Exception as e:
                self.error = type(e)
                return True
            else:
                self.time.append(time / number)
                self.repeat += 1
        return False

    def interrupt(self, e, repeat):
        if self.error is None:
            if self.repeat < repeat:
                self.error = type(e)
                return True
        return False

    def analyse(self):
        if self.time:
            mean = sum(self.time) / self.repeat

            sorted_time = sorted(self.time)

            i = self.repeat // 2
            if self.repeat & 1:
                median = sorted_time[i]
            else:
                median = (sorted_time[i] + sorted_time[i - 1]) / 2

            min_ = sorted_time[0]
            max_ = sorted_time[-1]

            std = (sum((time - mean) ** 2 for time in self.time) /
                   self.repeat) ** 0.5
        else:
            mean = median = min_ = max_ = std = None

        self.mean = mean
        self.median = median
        self.min = min_
        self.max = max_
        self.std = std

    def set_percent(self, max_mean, max_median):
        if self.time:
            mean_percent = self.mean / max_mean
            median_percent = self.median / max_median
        else:
            mean_percent = median_percent = None

        self.mean_percent = mean_percent
        self.median_percent = median_percent

    _null = '--'
    _units = (('s', 1.0), ('ms', 1e-3), ('μs', 1e-6), ('ns', 1e-9))

    def get_line(self, decimal, repeat):
        index = f'{self.index}'

        if isinstance(self.stmt, str):
            stmt = repr(self.stmt)
            if len(stmt) > 25:
                stmt = f"{stmt[:25]} ...'"
        elif callable(self.stmt):
            stmt = getattr(self.stmt, '__name__', self._null)
            if len(stmt) > 25:
                stmt = f'{stmt[:25]} ...'
        else:
            stmt = self._null

        if self.time:
            for unit, scale in self._units:
                if self.min >= scale:
                    break

            def format_time(second):
                return f'{second / scale:.{decimal}f}'

            mean = format_time(self.mean)
            mean_percent = f'{self.mean_percent:.2%}'
            mean_process = _get_process(self.mean_percent, 8)

            median = format_time(self.median)
            median_percent = f'{self.median_percent:.2%}'
            median_process = _get_process(self.median_percent, 8)

            min_ = format_time(self.min)
            max_ = format_time(self.max)
            std = format_time(self.std)

        else:
            unit = mean = mean_percent = mean_process = \
                median = median_percent = median_process = \
                min_ = max_ = std = self._null

        if self.error is not None:
            error = self.error.__name__
            if self.repeat < repeat:
                error = f'{error}(r={self.repeat})'
        else:
            error = self._null

        return [
            index, stmt, unit,
            mean, mean_percent, mean_process,
            median, median_percent, median_process,
            min_, max_, std,
            error
        ]


def compare(
        *stmts: Union[Sequence, str, Callable],
        setup: Union[str, Callable] = 'pass',
        globals: dict = None,
        number: int = 0,
        repeat: int = 5,
        sort_by: str = 'mean',
        reverse: bool = False,
        decimal: int = 3
) -> None:
    """
    Call timeit.timeit for several statements and provide comparison results.

    :param stmts: (statement, setup, globals) or a single statement to be
        compared.
    :param setup: default setup for each statement (default 'pass').
    :param globals: default globals for each statement (default globals()).
    :param number: number of loops per repetition (default: see below).
    :param repeat: number of repetitions (default 5).
    :param sort_by: the basis for sorting the results, which can be 'index',
        'mean', 'median', 'min', 'max' or 'std' (default 'mean').
    :param reverse: set True to sort the results in descending order (default
        False).
    :param decimal: number of decimal places reserved for results (default 3).
    :returns: None

    If number is not given or is less than or equal to 0, it defaults to a
    value that makes the total running time not too long. You can intentionally
    set it to a higher value to make the results more accurate.
    """

    start = perf_counter()

    timer_args = []

    for stmt in stmts:
        if isinstance(stmt, Sequence) and not isinstance(stmt, str):
            if len(stmt) > 3:
                raise ValueError(f'stmt expected at most 3 argument, '
                                 f'got {len(stmt)}')
            args = ['pass', setup, globals]
            for i, j in enumerate(stmt):
                if j is not None:
                    args[i] = j
        else:
            args = stmt, setup, globals

        timer_args.append(args)

    if not isinstance(number, int):
        raise TypeError(f'number must be a integer, not {type(number)}')
    if number < 0:
        number = 0

    if not isinstance(repeat, int):
        raise TypeError(f'repeat must be a integer, not {type(repeat)}')
    if repeat <= 0:
        repeat = 1

    if not isinstance(sort_by, str):
        raise TypeError(f'sort_by must be a string, not {type(sort_by)}')
    sort_by = sort_by.lower()
    if sort_by not in {'index', 'mean', 'median', 'min', 'max', 'std'}:
        raise ValueError(
            f'sort_by must be index, mean, median, min, max or '
            f'std, not {sort_by}')

    try:
        reverse = bool(reverse)
    except:
        raise TypeError(f'reverse must be a boolean, not {type(reverse)}')

    if not isinstance(decimal, int):
        raise TypeError(f'decimal must be a integer, not {type(decimal)}')
    if decimal < 0:
        decimal = 0

    # ________________________________________________________________________

    task = [_TimerTask(index, *args) for index, args in enumerate(timer_args)]

    print('timing now...')

    if number == 0:
        def autorange():
            i = 1
            while True:
                for j in 1, 2, 5:
                    number = i * j
                    time_taken = 0.0
                    all_error = True
                    for item in task:
                        time = item.autorange_timeit(number)
                        if time is not None:
                            time_taken += time
                            all_error = False
                    if all_error:
                        return 0
                    if time_taken > 0.2:
                        return number
                i *= 10

        try:
            number = autorange()
        except (KeyboardInterrupt, SystemExit) as e:
            for item in task:
                item.autorange_interrupt(e)

    task_num = len(task)
    total_repeat = task_num * repeat
    complete = 0
    error = sum(item.error is not None for item in task)
    _update_process(complete, total_repeat, error, task_num)

    try:
        for _ in range(repeat):
            for item in task:
                turn_error = item.timeit(number)
                if turn_error:
                    error += 1
                complete += 1
                _update_process(complete, total_repeat, error, task_num)

    except (KeyboardInterrupt, SystemExit) as e:
        for item in task:
            turn_error = item.interrupt(e, repeat)
            if turn_error:
                error += 1
        complete = total_repeat
        _update_process(complete, total_repeat, error, task_num)

    print()

    result = []
    max_mean = 0.0
    max_median = 0.0

    for item in task:
        item.analyse()

        if item.time:
            result.append(item)
            if item.mean > max_mean:
                max_mean = item.mean
            if item.median > max_median:
                max_median = item.median

    for item in task:
        item.set_percent(max_mean, max_median)

    result.sort(key=lambda item: getattr(item, sort_by), reverse=reverse)
    result.extend(item for item in task if not item.time)

    # ________________________________________________________________________

    # make table
    title = 'Comparison Results'
    header = ['Index', 'Stmt', 'Unit', 'Mean', 'Median', 'Min-Max', 'Std',
              'Error']
    sort_by_tip = '(SortBy)'
    if sort_by == 'index':
        header[0] += sort_by_tip
    elif sort_by == 'mean':
        header[3] += sort_by_tip
    elif sort_by == 'median':
        header[4] += sort_by_tip
    elif sort_by == 'min':
        header[5] = f'Min{sort_by_tip}-Max'
    elif sort_by == 'max':
        header[5] = f'Min-Max{sort_by_tip}'
    else:  # sort_by == 'std'
        header[6] += sort_by_tip
    header_cols = [1, 1, 1, 3, 3, 2, 1, 1]
    body = [task.get_line(decimal, repeat) for task in result]
    note = (f"{repeat} repetition{'s' if repeat != 1 else ''}, "
            f"{number:_} loop{'s' if number != 1 else ''} each.")
    _print_table(1, title, header, header_cols, body, note)

    end = perf_counter()
    print(f'finish at {end - start:.4f}s')


BLOCK = ' ▏▎▍▌▋▊▉█'


def _get_process(process, length):
    """Internal function."""

    if process <= 0.0:
        string = ' ' * length

    elif process >= 1.0:
        string = BLOCK[-1] * length

    else:
        d = 1.0 / length
        q = process // d
        block1 = BLOCK[-1] * int(q)

        r = process % d
        d2 = d / 8
        i = (r + d2 / 2) // d2
        block2 = BLOCK[int(i)]

        block3 = ' ' * (length - len(block1) - len(block2))

        string = f'{block1}{block2}{block3}'

    return string


def _update_process(complete, total_repeat, error, task_num):
    """Internal function."""

    process = _get_process(
        complete / total_repeat if total_repeat else 1.0, 16)
    string = (f'\r|{process}| {complete}/{total_repeat} completed, '
              f'{error}/{task_num} error')
    print(string, end='', flush=True)


def _print_table(number, title, header, header_cols, body, note):
    """Internal function."""
    title = f'Table {number}. {title}'

    body_width = [2] * sum(header_cols)
    for i, item in enumerate(zip(*body)):
        body_width[i] = max(map(len, item)) + 2

    header_width = []
    i = 0
    for s, col in zip(header, header_cols):
        hw = len(s) + 2
        if col == 1:
            bw = body_width[i]
            if hw > bw:
                body_width[i] = hw
            else:
                hw = bw
        else:
            bw = sum(body_width[i: i + col]) + col - 1
            if hw > bw:
                bw = hw - bw
                q, r = bw // col, bw % col
                for j in range(col):
                    if j < r:
                        dq = q + 1
                    else:
                        dq = q
                    body_width[i + j] += dq
            else:
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
    table_template = '\n'.join(lines)

    all_data = [title]
    all_data.extend(header)
    for row in body:
        all_data.extend(row)
    all_data.append(note)

    table_string = table_template.format(*all_data)

    print('\n', table_string, '\n', sep='')


def main() -> None:
    """
Usage:
  python timeit_compare.py [-s] [-n] [-r] [--sort-by] [--reverse] [-d] [-h] [--] [statements ...]

Options:
  -s, --setup       default setup for each statement (default 'pass').
  -n, --number      number of loops per repetition (default: see below).
  -r, --repeat      number of repetitions (default 5).
  --sort-by         the basis for sorting the results, which can be 'index', 'mean', 'median', 'min', 'max' or 'std' (default 'mean').
  --reverse         set to sort the results in descending order (default False).
  -d, --decimal     number of decimal places reserved for results (default 3).
  -h, --help        print this usage message and exit.
  --                separate options from statement, use when statement starts with -.
  statements        'statement#setup' or a single statement to be compared.

If -n is not given or is less than or equal to 0, it defaults to a value that makes the total running time not too long. You can intentionally set it to a higher value to make the results more accurate.
    """
    import sys
    args = sys.argv[1:]

    import getopt
    try:
        opts, args = getopt.getopt(
            args, 's:n:r:d:h',
            ['setup=', 'number=', 'repeat=', 'sort-by=', 'reverse',
             'decimal=', 'help'])
    except getopt.error as e:
        error = str(e)
    else:
        error = None
    if error is not None:
        raise getopt.error(f'{error}\nuse -h/--help for command line help')

    stmts = [a.split('#', 1) for a in args]
    setup = []
    globals = None
    number = 0
    repeat = 5
    sort_by = 'mean'
    reverse = False
    decimal = 3
    for k, v in opts:
        if k in ('-s', '--setup'):
            setup.append(v)
        elif k in ('-n', '--number'):
            number = int(v)
        elif k in ('-r', '--repeat'):
            repeat = int(v)
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
        *stmts,
        setup=setup,
        globals=globals,
        number=number,
        repeat=repeat,
        sort_by=sort_by,
        reverse=reverse,
        decimal=decimal
    )


if __name__ == '__main__':
    main()
