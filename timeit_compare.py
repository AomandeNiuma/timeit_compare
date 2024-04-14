"""
A method based on timeit that can help you to call timeit.timeit for several
statements and provide comparison results.

Function 'compare' only.
"""

from timeit import Timer, default_timer
from typing import Callable, Union

__all__ = ['compare']


class _TimerTask:
    """Internal class."""

    def __init__(self, index, stmt, setup, number):
        self.index = index
        self.stmt = stmt
        self.number = number

        try:
            timer = Timer(stmt, setup)
        except Exception as e:
            timer = None
            error = type(e)
        else:
            error = None
        self.timer = timer
        self.error = error

        self.time = []
        self.repeat = 0

    def timeit(self):
        if self.error is None:
            try:
                time = self.timer.timeit(self.number)
            except Exception as e:
                self.error = type(e)
                return True
            else:
                self.time.append(time)
                self.repeat += 1
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

    def get_line(self, decimal):
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

        repeat = f'{self.repeat}'

        if self.time:
            mean = f'{self.mean:.{decimal}f}s'
            mean_percent = f'{self.mean_percent:.2%}'
            mean_process = _get_process(self.mean_percent, 8)

            median = f'{self.median:.{decimal}f}s'
            median_percent = f'{self.median_percent:.2%}'
            median_process = _get_process(self.median_percent, 8)

            min_ = f'{self.min:.{decimal}f}s'
            max_ = f'{self.max:.{decimal}f}s'
            std = f'{self.std:.{decimal}f}'

        else:
            mean = mean_percent = mean_process = \
                median = median_percent = median_process = \
                min_ = max_ = std = self._null

        if self.error is not None:
            error = self.error.__name__
        else:
            error = self._null

        return [
            index, stmt, repeat,
            mean, mean_percent, mean_process,
            median, median_percent, median_process,
            min_, max_, std,
            error
        ]


def compare(
        *stmts: Union[str, Callable],
        setup: str = 'pass',
        number: int = 100_000,
        repeat: int = 10,
        sort_by: str = 'mean',
        reverse: bool = False,
        decimal: int = 4
) -> None:
    """
    Call timeit.timeit for several statements and provide comparison results.

    :param stmts: several statements to be compared,
    :param setup: setup statement,
    :param number: number of times per repetition,
    :param repeat: number of repetitions,
    :param sort_by: the basis for sorting the results, which can be 'index',
        'mean'(default), 'median', 'min', 'max' or 'std',
    :param reverse: set True to sort the results in descending order,
    :param: decimal: number of decimal places reserved for results,
    :returns: None.

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

    start = default_timer()

    if not isinstance(repeat, int):
        raise TypeError(f'repeat must be a integer, not {type(repeat)}')

    if not isinstance(sort_by, str):
        raise TypeError(f'sort_by must be a string, not {type(sort_by)}')

    sort_by = sort_by.lower()

    if sort_by not in {'index', 'mean', 'median', 'min', 'max', 'std'}:
        raise ValueError(
            f'sort_by must be index, mean, median, min, max or '
            f'std, not {sort_by}')

    if not isinstance(decimal, int):
        raise TypeError(f'decimal must be a integer, not {type(decimal)}')

    if decimal < 0:
        raise ValueError(f'decimal must be greater than 0')

    task = [_TimerTask(index, stmt, setup, number) for index, stmt in
            enumerate(stmts)]
    task_num = len(task)
    total_repeat = task_num * repeat
    complete = 0
    error = sum(item.error is not None for item in task)

    print('timing now...')
    _update_process(complete, total_repeat, error, task_num)

    try:
        for _ in range(repeat):
            for item in task:
                e = item.timeit()
                if e:
                    error += 1
                complete += 1
                _update_process(complete, total_repeat, error, task_num)

    except (KeyboardInterrupt, SystemExit) as e:
        error_type = type(e)
        for item in task:
            if item.error is None:
                if item.repeat < repeat:
                    item.error = error_type
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

    # make table
    title = 'Comparison Results'
    header = ['Index', 'Stmt', 'Repeat', 'Mean', 'Median', 'Min-Max', 'Std',
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
    body = [task.get_line(decimal) for task in result]
    note = f'{number:_} loops per repetition'
    _print_table(1, title, header, header_cols, body, note)

    end = default_timer()
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
    i = 0
    for col in header_cols:
        if col == 1:
            bw = body_width[i]
            split_border.append('─' * bw)
            split_border.append('┼')
        else:
            for bw in body_width[i: i + col]:
                split_border.append('─' * bw)
                split_border.append('┬')
            split_border[-1] = '┼'
        i += col
    split_border.pop()
    split_border = f"{dl}├{''.join(split_border)}┤{dr}"

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


if __name__ == '__main__':
    # Compare the running time of initialization methods
    # for several built-in data types
    compare(
        bool,
        bytearray,
        bytes,
        complex,
        dict,
        float,
        frozenset,
        int,
        list,
        set,
        str,
        tuple,
        number=1_000_000
    )
