from typing_extensions import TypeAlias, Union, Callable, Any, Literal, Dict, \
    List, TextIO, Optional, Iterable, Tuple

__all__ = ['TimeitResult', 'ComparisonResults', 'compare', 'cmp']

_Stmt: TypeAlias = Union[Callable[[], Any], str]
_Stat: TypeAlias = Literal['mean', 'median', 'min', 'max', 'stdev']
_Globals: TypeAlias = Dict[str, Any]


class TimeitResult:
    index: int
    stmt: _Stmt
    repeat: int
    number: int
    times: List[float]
    total_time: float
    mean: Optional[float]
    median: Optional[float]
    min: Optional[float]
    max: Optional[float]
    stdev: Optional[float]
    unreliable: bool

    def __init__(self, index: int, stmt: _Stmt, repeat: int, number: int,
                 times: List[float], total_time: float) -> None: ...

    def __str__(self) -> str: ...

    def print(self, precision: int = 2, file: TextIO = None) -> None: ...


class ComparisonResults:
    repeat: int
    number: int
    total_time: float
    unreliable: bool

    def __init__(self, repeat: int, number: int, results: List[TimeitResult]) \
            -> None: ...

    def __getitem__(self, item: int) -> TimeitResult: ...

    def __iter__(self) -> Iterable[TimeitResult]: ...

    def __reversed__(self) -> Iterable[TimeitResult]: ...

    def __len__(self) -> int: ...

    def __str__(self) -> str: ...

    def print(self, sort_by: Optional[_Stat] = 'mean', reverse: bool = False,
              precision: int = 2, percentage: Iterable[_Stat] = None,
              include: Iterable[int] = None, exclude: Iterable[int] = None,
              file: TextIO = None) -> None: ...


def compare(
        *timers: Union[
            _Stmt,
            Tuple[_Stmt],
            Tuple[_Stmt, Optional[_Stmt]],
            Tuple[_Stmt, Optional[_Stmt], Optional[_Globals]]
        ],
        setup: _Stmt = 'pass',
        globals: _Globals = None,
        repeat: int = 7,
        number: int = 0,
        total_time: float = 1.5,
        warmups: int = 1,
        show_progress: bool = False
) -> ComparisonResults: ...


def cmp(
        *timers: Union[
            _Stmt,
            Tuple[_Stmt],
            Tuple[_Stmt, Optional[_Stmt]],
            Tuple[_Stmt, Optional[_Stmt], Optional[_Globals]]
        ],
        setup: _Stmt = 'pass',
        globals: _Globals = None,
        repeat: int = 7,
        number: int = 0,
        total_time: float = 1.5,
        warmups: int = 1,
        show_progress: bool = True,
        sort_by: Optional[_Stat] = 'mean',
        reverse: bool = False,
        precision: int = 2,
        percentage: Iterable[_Stat] = None,
        file: TextIO = None
) -> None: ...
