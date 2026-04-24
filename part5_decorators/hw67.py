import functools
import json
from datetime import UTC, datetime
from typing import Any, NoReturn, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, *, func_name: str, block_time: datetime) -> None:
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class _BreakerState:
    __slots__ = ("block_time", "failure_count")

    def __init__(self) -> None:
        self.failure_count: int = 0
        self.block_time: datetime | None = None


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        errors: list[ValueError] = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)
        self._critical_count = critical_count
        self._time_to_recover = time_to_recover
        self._triggers_on = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        state = _BreakerState()
        func_name = f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self._check_open(state, func_name)
            try:
                result = func(*args, **kwargs)
            except self._triggers_on as exc:
                self._on_exception(state, func_name, exc)
            else:
                state.failure_count = 0
                return result

        return wrapper

    def _check_open(self, state: _BreakerState, func_name: str) -> None:
        if state.block_time is None:
            return
        elapsed = (datetime.now(UTC) - state.block_time).total_seconds()
        if elapsed >= self._time_to_recover:
            state.block_time = None
            state.failure_count = 0
            return
        raise BreakerError(TOO_MUCH, func_name=func_name, block_time=state.block_time)

    def _on_exception(self, state: _BreakerState, func_name: str, exc: Exception) -> NoReturn:
        state.failure_count += 1
        if state.failure_count < self._critical_count:
            raise exc
        state.block_time = datetime.now(UTC)
        raise BreakerError(TOO_MUCH, func_name=func_name, block_time=state.block_time) from exc


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
