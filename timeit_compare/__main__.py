#!/usr/bin/env python3

import argparse
import os
import sys

from . import __version__, _DEFAULT_STATS, compare


def main(args=None):
    parse = argparse.ArgumentParser(prog='python -m timeit_compare')

    parse.add_argument(
        '-v', '--version', action='version', version=__version__)
    parse.add_argument(
        '-a', '--add-timers', nargs='+', action='append', default=[],
        help="statement to be timed (statement) and statement to be executed "
             "once initially (setup, default: -s), separated by '-'. A "
             "multi-line statement can be given by passing multiple strings "
             "simultaneously in an argument.")
    parse.add_argument(
        '-s', '--setup', nargs='+', default=['pass'],
        help="the global default value for setup in -a (default: 'pass'). A "
             "multi-line statement is processed in the same way as -a.")
    parse.add_argument(
        '-r', '--repeat', type=int, default=7,
        help='how many times to repeat the timer (default: 7).')
    parse.add_argument(
        '-n', '--number', type=int, default=0,
        help='how many times to execute statement (default: estimated by -t).')
    parse.add_argument(
        '-t', '--time', type=float, default=1.5,
        help='if specified and no -n greater than 0 is specified, it will be '
             'used to estimate a -n so that the total execution time (in '
             'seconds) of all statements is approximately equal to this value '
             '(default: 1.5).')
    parse.add_argument(
        '--no-progress', action='store_true', help='no progress bar.')
    parse.add_argument(
        '--sort-by', choices=_DEFAULT_STATS, default='mean',
        help="statistic for sorting the results (default: 'mean').")
    parse.add_argument(
        '--no-sort', action='store_true', help='do not sort the results.')
    parse.add_argument(
        '--reverse', action='store_true',
        help='sort the results in descending order.')
    parse.add_argument(
        '--stats', choices=_DEFAULT_STATS, nargs='*', default=None,
        help='statistics in the column headers of the table (default: all '
             'statistics in default order).')
    parse.add_argument(
        '--percentage', choices=_DEFAULT_STATS, nargs='*', default=None,
        help='statistics showing percentage (default: same as --sort-by).')
    parse.add_argument(
        '-p', '--precision', type=int, default=2,
        help='digits precision of the results (default: 2).')

    args = parse.parse_args(args)

    add_timers = []
    for a in args.add_timers:
        if '-' in a:
            i = a.index('-')
            a = ['\n'.join(a[:i]), '\n'.join(a[i + 1:])]
        else:
            a = '\n'.join(a)
        add_timers.append(a)

    # Include the current directory, so that local imports work
    sys.path.insert(0, os.curdir)

    try:
        compare(
            *add_timers,
            setup='\n'.join(args.setup),
            globals=None,
            add_stats=(),
            repeat=args.repeat,
            number=args.number,
            time=args.time,
            show_progress=not args.no_progress,
            sort_by=args.sort_by if not args.no_sort else None,
            reverse=args.reverse,
            stats=args.stats,
            percentage=args.percentage,
            precision=args.precision
        )

    except:
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
