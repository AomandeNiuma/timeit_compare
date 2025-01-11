#!/usr/bin/env python3

import argparse
import os
import sys

from . import __version__, _stats, cmp


def main(args=None):
    parse = argparse.ArgumentParser(prog='python -m timeit_compare')

    parse.add_argument(
        '-v', '--version', action='version', version=__version__)
    parse.add_argument(
        '-', '--stmt', nargs='+', action='append', default=[],
        help='statement to be timed. A multi-line statement can be given by '
             'passing multiple strings simultaneously in an argument.')
    parse.add_argument(
        '-s', '--setup', nargs='*', action='append', default=[],
        help="statement to be executed once initially for the last --stmt "
             "argument, if there are no --stmt arguments before this, it "
             "indicates the default setup statement for all --stmt (default: "
             "'pass'). A multi-line statement is processed in the same way as "
             "--stmt.")
    parse.add_argument(
        '-r', '--repeat', type=int, default=7,
        help='how many times to repeat the timers (default: 7).')
    parse.add_argument(
        '-n', '--number', type=int, default=0,
        help='how many times to execute statement (default: estimated by '
             '-t).')
    parse.add_argument(
        '-t', '--total-time', type=float, default=1.5,
        help='if specified and no -n greater than 0 is specified, it will be '
             'used to estimate a -n so that the total execution time (in '
             'seconds) of all statements is approximately equal to this value '
             '(default: 1.5).')
    parse.add_argument(
        '-w', '--warmups', type=int, default=1,
        help='how many times to warm up the timers (default: 1).')
    parse.add_argument(
        '--no-progress', action='store_true', help='no progress bar.')
    parse.add_argument(
        '--sort-by', choices=_stats, default='mean',
        help="statistic for sorting the results (default: 'mean').")
    parse.add_argument(
        '--no-sort', action='store_true', help='do not sort the results.')
    parse.add_argument(
        '--reverse', action='store_true',
        help='sort the results in descending order.')
    parse.add_argument(
        '-p', '--precision', type=int, default=2,
        help='digits precision of the results, ranging from 1 to 8 (default: '
             '2).')
    parse.add_argument(
        '--percentage', choices=_stats, nargs='*', default=None,
        help='statistics showing percentage (default: same as --sort-by).')

    if args is None:
        args = sys.argv[1:]
    pargs = parse.parse_args(args)

    timers = []
    setup = []
    iter_stmts = iter(pargs.stmt)
    iter_setup = iter(pargs.setup)
    for a in args:
        if a in ('-', '--stmt'):
            stmt = next(iter_stmts)
            timers.append([stmt, None, None])
        elif a in ('-s', '--setup'):
            s = next(iter_setup)
            if not timers:
                setup.extend(s)
            else:
                last_timer = timers[-1]
                if last_timer[1] is None:
                    last_timer[1] = []
                last_timer[1].extend(s)
    setup = '\n'.join(setup) if setup else 'pass'
    for timer in timers:
        timer[0] = '\n'.join(timer[0])
        if timer[1] is not None:
            timer[1] = '\n'.join(timer[1]) if timer[1] else 'pass'

    # include the current directory, so that local imports work
    sys.path.insert(0, os.curdir)

    try:
        cmp(
            *timers,
            setup=setup,
            globals={},
            repeat=pargs.repeat,
            number=pargs.number,
            total_time=pargs.total_time,
            warmups=pargs.warmups,
            show_progress=not pargs.no_progress,
            sort_by=pargs.sort_by if not pargs.no_sort else None,
            reverse=pargs.reverse,
            precision=pargs.precision,
            percentage=pargs.percentage,
            file=None
        )

    except:
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
