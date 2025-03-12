"""
Separate the unimportant code that controls the output of the program from the
main part.
"""

import itertools

_stats = ('mean', 'median', 'min', 'max', 'stdev')


class TimeitResultOutput:
    """Internal class."""

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
            else:
                line.append('-')

            if stat in max_value:
                percent = value / max_value[stat] if max_value[stat] else 1.0

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

        if isinstance(self.stmt, str):
            stmts = self.stmt.splitlines()
            # remove the blank line before and after the statement
            while stmts and (not stmts[0] or stmts[0].isspace()):
                stmts.pop(0)
            while stmts and (not stmts[-1] or stmts[-1].isspace()):
                stmts.pop()
            if not stmts:
                line.append('')
                lines = [line]
            else:
                it = map(repr, stmts)
                line.append(next(it)[1:-1])
                lines = [line]
                for stmt in it:
                    line = [''] * (len(line) - 1)
                    line.append(stmt[1:-1])
                    lines.append(line)
        elif callable(self.stmt) and hasattr(self.stmt, '__name__'):
            line.append(self.stmt.__name__ + '()')
            lines = [line]
        else:
            line.append('')
            lines = [line]

        return lines

    def _table(self, precision):
        """Internal function."""
        title = 'Timeit Result (unit: s)'
        header = ['Idx', *(stat.title() for stat in _stats), 'Stmt']
        header_cols = [1] * len(header)
        body = self._get_line(precision, {})
        body_aligns = ['^'] * sum(header_cols)
        body_aligns[-1] = '<'
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
            colour_red = '\x1b[31m'
            colour_reset = '\x1b[0m'
            table = table.splitlines()
            i = next(i for i in itertools.count(4) if table[i][1] == '─') + 1
            for j in range(i, i + len(body)):
                table[j] = f'{colour_red}{table[j]}{colour_reset}'
            i = next(i for i in itertools.count(-2, -1) if table[i][1] == '*')
            for j in range(i, -1):
                table[j] = f'{colour_red}{table[j]}{colour_reset}'
            table = '\n'.join(table)
        return table


class ComparisonResultsOutput:
    """Internal class."""

    def _table(self, sort_by, reverse, precision, percentage, include, exclude):
        """Internal function."""
        if include is None and exclude is None:
            results = self._results.copy()
            total_time = self.total_time
            unreliable = self.unreliable
        else:
            if include is not None:
                results = [result for result in self._results
                           if result.index in include]
            else:
                results = [result for result in self._results
                           if result.index not in exclude]
            total_time = sum(result.total_time for result in results)
            unreliable = any(result.unreliable for result in results)

        title = 'Comparison Results (unit: s)'

        header = ['Idx', *(stat.title() for stat in _stats), 'Stmt']
        if sort_by is not None:
            i = 1 + _stats.index(sort_by)
            header[i] += ' ↓' if not reverse else ' ↑'

            if not (sort_by == 'stdev' and self.repeat < 2):
                results.sort(key=lambda result: getattr(result, sort_by),
                             reverse=reverse)

        if 'stdev' in percentage and self.repeat < 2:
            percentage.remove('stdev')

        header_cols = [1] * len(header)
        for i, stat in enumerate(_stats, 1):
            if stat in percentage:
                header_cols[i] = 3

        max_value = dict.fromkeys(percentage, 0.0)
        for result in results:
            for stat in percentage:
                value = getattr(result, stat)
                if value > max_value[stat]:
                    max_value[stat] = value

        body = []
        body_rows = []
        for result in results:
            lines = result._get_line(precision, max_value)
            body.extend(lines)
            body_rows.append(len(lines))

        body_aligns = ['^'] * sum(header_cols)
        body_aligns[-1] = '<'

        note = (f"{self.repeat} run{'s' if self.repeat != 1 else ''}, "
                f"{self.number} loop{'s' if self.number != 1 else ''} each, "
                f"total time {total_time:#.4g}s")
        if unreliable:
            note += (
                '\n*: Marked results are likely unreliable as the worst '
                'time was more than four times slower than the best time.')

        table = _table(title, header, header_cols, body, body_aligns, note)

        if unreliable:
            # mark unreliable tips in red
            colour_red = '\x1b[31m'
            colour_reset = '\x1b[0m'

            table = table.splitlines()

            i = next(i for i in itertools.count(4) if table[i][1] == '─') + 1
            for result, row in zip(results, body_rows):
                if result.unreliable:
                    for j in range(i, i + row):
                        table[j] = f'{colour_red}{table[j]}{colour_reset}'
                i += row

            i = next(i for i in itertools.count(-2, -1) if table[i][1] == '*')
            for j in range(i, -1):
                table[j] = f'{colour_red}{table[j]}{colour_reset}'

            table = '\n'.join(table)

        return table


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


def progress(task_num, length):
    """Internal function."""
    for i in range(task_num + 1):
        template = (f'\r|{{progress_bar}}| '
                    f'{{completed_num}}/{task_num} completed')
        percent = i / task_num if task_num else 1.0
        progress = template.format(
            progress_bar=_progress_bar(percent, length),
            completed_num=i)
        yield progress


def _wrap(text, width):
    """Internal function."""
    result = []
    for line in text.splitlines():
        line = line.strip(' ')
        if not line:
            result.append('')
            continue
        while line:
            if len(line) <= width:
                result.append(line)
                break
            split = line.rfind(' ', 0, width + 1)
            if split == -1:
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

    blank_line = ' ' * (table_width + 2)
    title_line = f' {{:^{table_width}}} '
    header_line = f"   {'   '.join(f'{{:^{hw}}}' for hw in header_width)}   "
    body_line = '   '.join(
        f'{{:{ba}{bw}}}' for ba, bw in zip(body_aligns, body_width))
    body_line = f'   {body_line}   '
    note_line = f' {{:<{table_width}}} '
    border = f" {'─' * table_width} "

    template = '\n'.join(
        (
            blank_line,
            *(title_line,) * len(title),
            border,
            header_line,
            border,
            *(body_line,) * len(body),
            border,
            *(note_line,) * len(note),
            blank_line
        )
    )

    return template.format(*itertools.chain(title, header, *body, note))
