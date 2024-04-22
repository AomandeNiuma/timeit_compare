"""
A method based on timeit that can help you to call timeit.timeit for several
statements and provide comparison results.

In-Script usage:
    from timeit_compare import compare

    compare(*stmts[, setup][, globals][, repeat][, number][, time][, sort_by]
        [, reverse][, decimal])

See parameters in the function compare.

Command line usage:
    python -m timeit_compare [-s] [-r] [-n] [-t] [--sort-by] [--reverse] [-d]
        [-h] [--] [statements ...]

See options in the function main.

Note that if an error occurs during the operation of a statement, the program
will stop timing this statement, display the error type in the error cell of
the final results, and then continue to time other statements without errors.

If you actively terminate the program, all statements immediately stop timing
and then output the comparison results of the data already obtained.

To ensure a good user experience, the output terminal should use a font that
has a fixed width and supports unicode characters. Additionally, it is best not
to automatically wrap lines of text.
"""

import statistics
from time import perf_counter
from timeit import Timer
from typing import Sequence, Callable, Union

__all__ = ['compare']


def _percent(a, b):
    """Internal function."""
    return a / b if b else 1.0


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
        self.total_time = 0.0

    def pre_timeit(self, number):
        if self.error is None:
            try:
                time = self.timer.timeit(number)
            except Exception as e:
                self.error = type(e)
            else:
                return time

    def pre_interrupt(self, e):
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
                self.total_time += time
        return False

    def interrupt(self, e, repeat):
        if self.error is None:
            if len(self.time) < repeat:
                self.error = type(e)
                return True
        return False

    def stat(self):
        if self.time:
            mean = statistics.mean(self.time)
            median = statistics.median(self.time)
            min_ = min(self.time)
            max_ = max(self.time)
            if len(self.time) >= 2:
                std = statistics.stdev(self.time, mean)
            else:
                std = None
        else:
            mean = median = min_ = max_ = std = None

        self.mean = mean
        self.median = median
        self.min = min_
        self.max = max_
        self.std = std

    def set_percent(self, max_mean, max_median):
        if self.time:
            mean_percent = _percent(self.mean, max_mean)
            median_percent = _percent(self.median, max_median)
        else:
            mean_percent = median_percent = None

        self.mean_percent = mean_percent
        self.median_percent = median_percent

    _null = '--'
    _units = (('s', 1.0), ('ms', 1e-3), ('μs', 1e-6), ('ns', 1e-9))

    def get_line(self, decimal, repeat):
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
            stmt = f'{stmt[:25]} ...'

        if self.time:
            for unit, scale in self._units:
                if self.min >= scale:
                    break

            def format_time(second):
                return f'{second / scale:.{decimal}f}'

            mean = format_time(self.mean)
            mean_percent = f'{self.mean_percent:.2%}'
            mean_process = _process_bar(self.mean_percent, 8)

            median = format_time(self.median)
            median_percent = f'{self.median_percent:.2%}'
            median_process = _process_bar(self.median_percent, 8)

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
        repeat: int = 5,
        number: int = 0,
        time: Union[float, int] = 1.0,
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
    :param repeat: how many times to repeat the timer (default 5).
    :param number: how many times to execute statement (default 0, estimated by
        time).
    :param time: approximate total running time of all statements in seconds
        (default 1.0). Ignored when number is greater than 0.
    :param sort_by: the basis for sorting the results, which can be 'index',
        'mean', 'median', 'min', 'max' or 'std' (default 'mean').
    :param reverse: set True to sort the results in descending order (default
        False).
    :param decimal: number of decimal places reserved for results (default 3).
    :returns: None
    """
    timer_args = []
    for stmt in stmts:
        if isinstance(stmt, Sequence) and not isinstance(stmt, str):
            if len(stmt) > 3:
                raise ValueError(
                    f'stmt expected at most 3 argument, got {len(stmt)}')
            args = ['pass', setup, globals]
            for i, j in enumerate(stmt):
                if j is not None:
                    args[i] = j
        else:
            args = stmt, setup, globals
        timer_args.append(args)

    if not isinstance(repeat, int):
        raise TypeError(f'repeat must be a integer, not {type(repeat)}')
    if repeat <= 0:
        repeat = 1

    if not isinstance(number, int):
        raise TypeError(f'number must be a integer, not {type(number)}')
    if number < 0:
        number = 0

    if not isinstance(time, (float, int)):
        raise TypeError(f'time must be a real number, not {type(time)}')
    if time < 0.0:
        time = 0.0

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
        def estimate():
            n = 1
            while True:
                total_t = 0.0
                all_error = True
                for item in task:
                    t = item.pre_timeit(n)
                    if t is not None:
                        total_t += t
                        all_error = False
                if all_error:
                    return 0
                if total_t > 0.2:
                    return max(round((time * (n / total_t)) / repeat), 1)
                n <<= 1

        try:
            number = estimate()
        except (KeyboardInterrupt, SystemExit) as e:
            for item in task:
                item.pre_interrupt(e)

    task_num = len(task)
    total_repeat = task_num * repeat
    complete = 0
    error = sum(item.error is not None for item in task)
    _print_process(complete, total_repeat, error, task_num)

    try:
        for _ in range(repeat):
            for item in task:
                turn_error = item.timeit(number)
                if turn_error:
                    error += 1
                complete += 1
                _print_process(complete, total_repeat, error, task_num)

    except (KeyboardInterrupt, SystemExit) as e:
        for item in task:
            turn_error = item.interrupt(e, repeat)
            if turn_error:
                error += 1
        complete = total_repeat
        _print_process(complete, total_repeat, error, task_num)

    print()

    max_mean = 0.0
    max_median = 0.0
    total_time = 0.0

    for item in task:
        item.stat()

        if item.time:
            if item.mean > max_mean:
                max_mean = item.mean
            if item.median > max_median:
                max_median = item.median
            total_time += item.total_time

    for item in task:
        item.set_percent(max_mean, max_median)

    result = [item for item in task if item.time]
    result.sort(key=lambda item: getattr(item, sort_by), reverse=reverse)
    result.extend([item for item in task if not item.time])

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
            f"{number} loop{'s' if number != 1 else ''} each, "
            f"total runtime {total_time:.4f}s")
    _print_table(1, title, header, header_cols, body, note)


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


def _print_process(complete, total_repeat, error, task_num):
    """Internal function."""
    process = _process_bar(_percent(complete, total_repeat), 16)
    string = (f'\r|{process}| {complete}/{total_repeat} completed, '
              f'{error}/{task_num} error')
    print(string, end='', flush=True)


def _print_table(number, title, header, header_cols, body, note):
    """Internal function."""
    title = f'Table {number}. {title}'

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
    table_template = '\n'.join(lines)

    all_data = [title]
    all_data.extend(header)
    for row in body:
        all_data.extend(row)
    all_data.append(note)
    table_string = table_template.format(*all_data)

    print(table_string)


def main() -> None:
    """Usage:
  python -m timeit_compare [-s] [-r] [-n] [-t] [--sort-by] [--reverse] [-d] [-h] [--] [statements ...]

Options:
  -s, --setup       default setup for each statement (default 'pass').
  -r, --repeat      how many times to repeat the timer (default 5).
  -n, --number      how many times to execute statement (default 0, estimated by time).
  -t, --time        approximate total running time of all statements in seconds (default 1.0). Ignored when number is greater than 0.
  --sort-by         the basis for sorting the results, which can be 'index', 'mean', 'median', 'min', 'max' or 'std' (default 'mean').
  --reverse         set to sort the results in descending order (default False).
  -d, --decimal     number of decimal places reserved for results (default 3).
  -h, --help        print this usage message and exit.
  --                separate options from statement, use when statement starts with -.
  statements        'statement#setup' or a single statement to be compared."""
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

    stmts = [a.split('#', 1) for a in args]
    setup = []
    globals = None
    repeat = 5
    number = 0
    time = 1.0
    sort_by = 'mean'
    reverse = False
    decimal = 3
    for k, v in opts:
        if k in ('-s', '--setup'):
            setup.append(v)
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
        *stmts,
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
