from typing_extensions import (NamedTuple, TypeAlias, Union, Callable, Any,
                               Dict, Tuple, Optional, Iterable, Sequence)

__all__ = ['TimerResult', 'Compare', 'compare']

_TimerId: TypeAlias = int
_Stmt: TypeAlias = Union[Callable[[], Any], str]
_Stat: TypeAlias = str
_StatFunc: TypeAlias = Callable[
    [Tuple[float, ...]], Optional[Union[float, int]]]


class TimerResult(NamedTuple):
    id: _TimerId
    repeat: int
    stats: NamedTuple
    time: Tuple[float, ...]
    number: int


class Compare:
    def __init__(self) -> None: ...

    def add_timer(
            self,
            stmt: _Stmt,
            setup: _Stmt = 'pass',
            globals: Dict[str, Any] = None
    ) -> _TimerId: ...

    def del_timer(self, id: _TimerId) -> None: ...

    def add_stat(self, stat: _Stat, func: _StatFunc) -> None: ...

    def del_stat(self, stat: _Stat) -> None: ...

    def run(
            self,
            repeat: int = 7,
            number: int = 0,
            time: Union[float, int] = 1.5,
            show_progress: bool = False,
    ) -> None: ...

    def get_result(self, id: _TimerId) -> TimerResult: ...

    def get_min(self, stat: _Stat = 'mean') -> Optional[TimerResult]: ...

    def get_max(self, stat: _Stat = 'mean') -> Optional[TimerResult]: ...

    def print_results(
            self,
            include: Iterable[_TimerId] = None,
            exclude: Iterable[_TimerId] = None,
            sort_by: Optional[_Stat] = 'mean',
            reverse: bool = False,
            stats: Union[_Stat, Sequence[_Stat]] = None,
            percentage: Union[_Stat, Iterable[_Stat]] = None,
            precision: int = 2
    ) -> None: ...


def compare(
        *add_timers: Union[
            _Stmt,
            Tuple[_Stmt],
            Tuple[_Stmt, Optional[_Stmt]],
            Tuple[_Stmt, Optional[_Stmt], Optional[Dict[str, Any]]]
        ],
        setup: _Stmt = 'pass',
        globals: Dict[str, Any] = None,
        add_stats: Sequence[Tuple[_Stat, _StatFunc]] = (),
        repeat: int = 7,
        number: int = 0,
        time: Union[float, int] = 1.5,
        show_progress: bool = True,
        sort_by: Optional[_Stat] = 'mean',
        reverse: bool = False,
        stats: Union[_Stat, Sequence[_Stat]] = None,
        percentage: Union[_Stat, Iterable[_Stat]] = None,
        precision: int = 2
) -> None: ...
