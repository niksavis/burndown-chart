import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


RATE_LIMIT_MAX_TOKENS = 100
RATE_LIMIT_REFILL_RATE = 10
RATE_LIMIT_REFILL_INTERVAL_SECONDS = 1.0


MAX_RETRY_ATTEMPTS = 5
INITIAL_RETRY_DELAY_SECONDS = 1.0
MAX_RETRY_DELAY = 32.0


class TokenBucket:
    def __init__(
        self,
        max_tokens: int = RATE_LIMIT_MAX_TOKENS,
        refill_rate: float = RATE_LIMIT_REFILL_RATE,
    ):

        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens
        self.last_refill_time = time.time()

    def _refill(self):

        now = time.time()
        time_passed = now - self.last_refill_time

        tokens_to_add = time_passed * self.refill_rate

        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:

        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_for_token(self, tokens: int = 1) -> float:

        wait_start = time.time()

        while not self.consume(tokens):
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate

            time.sleep(min(wait_time, 1.0))

        return time.time() - wait_start


_rate_limiter = TokenBucket()


def get_rate_limiter() -> TokenBucket:

    return _rate_limiter


def reset_rate_limiter():

    global _rate_limiter
    _rate_limiter = TokenBucket()


def retry_with_backoff(
    func,
    *args,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    initial_delay: float = INITIAL_RETRY_DELAY_SECONDS,
    max_delay: float = MAX_RETRY_DELAY,
    **kwargs,
) -> tuple[bool, Any]:

    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = func(*args, **kwargs)

            if attempt > 1:
                logger.info(f"[OK] Request succeeded after {attempt} attempts")
            return True, result

        except Exception as e:
            last_exception = e
            error_msg = str(e)

            is_retryable = (
                "429" in error_msg
                or "5" in error_msg[:1]
                or "timeout" in error_msg.lower()
                or "connection" in error_msg.lower()
            )

            if not is_retryable or attempt >= max_attempts:
                logger.warning(
                    f"[X] Request failed after {attempt} attempts: {error_msg}"
                )
                return False, e

            logger.warning(
                f"[WARN] Attempt {attempt}/{max_attempts} failed: {error_msg}"
            )
            logger.info(f"[Pending] Retrying in {delay:.1f}s... (exponential backoff)")

            time.sleep(delay)

            delay = min(delay * 2, max_delay)

    return False, last_exception
