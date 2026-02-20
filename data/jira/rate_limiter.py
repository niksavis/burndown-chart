"""
JIRA API Rate Limiter Module

Provides rate limiting and retry logic for JIRA API requests using:
- Token Bucket Algorithm: Smooth rate limiting with burst support
- Exponential Backoff: Automatic retries for transient failures

Architecture:
- TokenBucket class: Rate limiter implementation (10 req/sec, 100 burst)
- retry_with_backoff: Retry wrapper for API calls with exponential backoff
- Global instance: Shared rate limiter across all JIRA requests

Usage:
    from data.jira.rate_limiter import get_rate_limiter, retry_with_backoff

    # Rate limit requests
    rate_limiter = get_rate_limiter()
    rate_limiter.wait_for_token()
    response = requests.get(...)

    # Retry on failures
    success, response = retry_with_backoff(requests.get, url, headers=headers)
"""

import time
from typing import Any

from configuration import logger

#######################################################################
# RATE LIMITING CONFIGURATION (T052)
#######################################################################

# Token Bucket Algorithm Configuration
# -------------------------------------
# Why Token Bucket?
# - Allows burst traffic: 100 requests immediately, then steady rate
# - Better user experience than strict rate limiting (no delays for small batches)
# - Prevents API abuse while maintaining responsiveness
#
# Configuration Rationale:
# - MAX_TOKENS=100: Average JIRA query returns 100-1000 issues (1-10 pages)
#   * Allows fetching typical query in one burst without delays
# - REFILL_RATE=10: JIRA Cloud typically allows 300-1000 req/min
#   * 10 req/sec = 600 req/min (conservative to stay well below limits)
#   * Gives 100 requests per 10 seconds on average
# - Result: Fast for small queries, throttled for large datasets

RATE_LIMIT_MAX_TOKENS = 100  # Maximum requests allowed in burst
RATE_LIMIT_REFILL_RATE = 10  # Tokens added per second (10 req/sec = 100 req/10sec)
RATE_LIMIT_REFILL_INTERVAL = 1.0  # Refill interval in seconds

#######################################################################
# RETRY CONFIGURATION (T053)
#######################################################################

# Exponential Backoff Configuration
# ----------------------------------
# Why Exponential Backoff?
# - Transient errors (network glitches, rate limits) often resolve quickly
# - Exponential delays prevent overwhelming struggling servers
# - Gives system time to recover without giving up too early
#
# Configuration Rationale:
# - MAX_ATTEMPTS=5: Covers 1s + 2s + 4s + 8s + 16s = 31s total retry time
#   * Enough time for transient issues to resolve
#   * Not so long that user waits forever
# - DELAYS: 1s → 2s → 4s → 8s → 16s → 32s (capped)
#   * Quick initial retry (1s) for fast recovery
#   * Exponential growth prevents hammering API
#   * 32s cap prevents excessive wait times
# - Retryable Errors: 429 rate limits, 5xx server errors, timeouts, connection errors
#   * These are transient - likely to succeed if we wait and retry
#   * 4xx client errors (except 429) are not retried - they indicate bad requests

MAX_RETRY_ATTEMPTS = 5  # Maximum number of retry attempts
INITIAL_RETRY_DELAY = 1.0  # Initial delay in seconds (doubles each retry)
MAX_RETRY_DELAY = 32.0  # Maximum delay between retries (cap exponential growth)

#######################################################################
# RATE LIMITING - TOKEN BUCKET ALGORITHM (T052)
#######################################################################


class TokenBucket:
    """
    Token Bucket algorithm for rate limiting API requests.

    **How It Works:**
    1. Bucket starts with max_tokens (100) - these are "permission slips" for requests
    2. Each API request consumes 1 token from the bucket
    3. Bucket refills at refill_rate (10 tokens/second) continuously
    4. If bucket is empty, requests must wait for refill

    **Why This Approach:**
    - Allows bursts: User can make 100 requests immediately (good UX for small queries)
    - Prevents abuse: After burst, throttled to 10 req/sec (prevents API overload)
    - Smooth rate limiting: Better than hard limits (no sudden blocks)

    **Example Scenario:**
    - User fetches JIRA data (300 issues = 3 API calls with 100/page)
    - First 3 calls: Instant (100 tokens available, use 3, 97 remain)
    - If user refreshes immediately: Uses 3 more tokens (94 remain)
    - If 100 requests made quickly: Bucket empty, next request waits ~0.1s for refill
    - Steady state: Can make 10 requests per second continuously

    **Configuration:**
    - max_tokens=100: See RATE_LIMIT_MAX_TOKENS comment for rationale
    - refill_rate=10: See RATE_LIMIT_REFILL_RATE comment for rationale
    """

    def __init__(
        self,
        max_tokens: int = RATE_LIMIT_MAX_TOKENS,
        refill_rate: float = RATE_LIMIT_REFILL_RATE,
    ):
        """
        Initialize token bucket for rate limiting.

        Args:
            max_tokens: Maximum tokens (requests) available in bucket (burst capacity)
            refill_rate: Tokens added per second (steady-state rate limit)
        """
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate
        self.tokens = max_tokens  # Start with full bucket (allow immediate burst)
        self.last_refill_time = time.time()

    def _refill(self):
        """
        Refill tokens based on time elapsed since last refill.

        **Algorithm:**
        1. Calculate time passed since last refill
        2. Multiply time by refill_rate to get tokens to add
        3. Add tokens but cap at max_tokens (bucket can't overflow)
        4. Update last_refill_time to now

        **Example:**
        - Last refill: 5 seconds ago
        - Refill rate: 10 tokens/second
        - Tokens to add: 5 * 10 = 50 tokens
        - If bucket had 30 tokens, now has min(100, 30+50) = 80 tokens
        """
        now = time.time()
        time_passed = now - self.last_refill_time

        # Calculate tokens to add based on time passed
        tokens_to_add = time_passed * self.refill_rate

        # Add tokens but don't exceed max (bucket capacity is limited)
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_refill_time = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from bucket (non-blocking).

        Args:
            tokens: Number of tokens to consume (default 1 for single request)

        Returns:
            True if tokens consumed successfully, False if not enough tokens

        **Usage:**
        - Used by wait_for_token() internally
        - Can be used directly for non-blocking rate limit checks
        """
        self._refill()  # Always refill before checking

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_for_token(self, tokens: int = 1) -> float:
        """
        Wait until enough tokens are available and consume them (blocking).

        **This is the main rate limiting function used by JIRA API calls.**

        Args:
            tokens: Number of tokens needed (usually 1 per API request)

        Returns:
            Time waited in seconds (0 if tokens immediately available)

        **Algorithm:**
        1. Try to consume tokens with consume()
        2. If successful: Return immediately (no wait)
        3. If failed: Calculate wait time based on refill rate
        4. Sleep and retry until tokens available

        **Example Scenarios:**
        - Bucket has 50 tokens, need 1: Returns immediately, 0 wait time
        - Bucket has 0 tokens, need 1: Waits 0.1s (1/10 refill rate), then returns
        - Bucket has 0 tokens, need 5: Waits 0.5s (5/10 refill rate), then returns
        """
        wait_start = time.time()

        while not self.consume(tokens):
            # Calculate how long to wait for next token
            tokens_needed = tokens - self.tokens
            wait_time = tokens_needed / self.refill_rate

            # Sleep for the calculated time (capped at 1 second intervals for responsiveness)
            time.sleep(min(wait_time, 1.0))

        return time.time() - wait_start


# Global rate limiter instance (shared across all JIRA requests)
# This ensures rate limiting is coordinated across all fetch operations
_rate_limiter = TokenBucket()


def get_rate_limiter() -> TokenBucket:
    """
    Get the global rate limiter instance.

    **Usage in JIRA API calls:**
    ```python
    rate_limiter = get_rate_limiter()
    rate_limiter.wait_for_token()  # Block until token available
    response = requests.get(...)  # Make request
    ```
    """
    return _rate_limiter


def reset_rate_limiter():
    """
    Reset the global rate limiter (useful for testing).

    Creates a new TokenBucket with full tokens, resets all state.
    """
    global _rate_limiter
    _rate_limiter = TokenBucket()


#######################################################################
# RETRY LOGIC - EXPONENTIAL BACKOFF (T053)
#######################################################################


def retry_with_backoff(
    func,
    *args,
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    initial_delay: float = INITIAL_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY,
    **kwargs,
) -> tuple[bool, Any]:
    """
    Retry a function with exponential backoff on transient failures.

    **Purpose:**
    Automatically retry API calls when they fail due to temporary issues:
    - Network glitches (connection errors, timeouts)
    - JIRA rate limiting (429 Too Many Requests)
    - Server overload (500, 502, 503, 504 errors)

    **How It Works:**
    1. Try to execute function
    2. If succeeds: Return result immediately
    3. If fails with retryable error: Wait and try again
    4. Increase wait time exponentially: 1s → 2s → 4s → 8s → 16s → 32s
    5. Give up after 5 attempts (total ~31 seconds of waiting)

    **Why Exponential Backoff:**
    - Quick recovery: 1s initial delay catches fast transient errors
    - Prevents hammering: Doubling delay gives system time to recover
    - Capped delays: 32s maximum prevents excessive waiting
    - Reasonable total time: ~31s total retry time is long enough for transient issues

    **Retryable vs Non-Retryable Errors:**
    - [OK] Retry: 429 (rate limit), 5xx (server errors), timeouts, connection errors
    - [X] Don't retry: 4xx client errors (except 429) - these indicate bad requests

    **Example Scenario:**
    - Attempt 1: Network timeout → Wait 1s, retry
    - Attempt 2: 503 Service Unavailable → Wait 2s, retry
    - Attempt 3: Success! → Return result
    - Total time: 3 seconds (saved from permanent failure)

    **Integration with Rate Limiting:**
    This works alongside TokenBucket rate limiting:
    - Rate limiter: Prevents making too many requests (proactive)
    - Retry logic: Handles failures when they happen (reactive)
    - Together: Robust API integration that handles both planned and unplanned issues

    Args:
        func: Function to retry (typically requests.get, requests.post, etc.)
        *args: Positional arguments for function
        max_attempts: Maximum number of retry attempts (default: 5)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay between retries (default: 32.0)
        **kwargs: Keyword arguments for function

    Returns:
        Tuple of (success: bool, result: Any)
        - success=True: Function succeeded, result contains return value
        - success=False: All retries exhausted, result contains last exception

    **Usage Example:**
    ```python
    from data.jira.rate_limiter import retry_with_backoff

    # Wrap API call with retry logic
    success, response = retry_with_backoff(
        requests.get,
        url,
        headers=headers,
        params=params,
        timeout=30
    )

    if success:
        data = response.json()
    else:
        logger.error(f"Failed after retries: {response}")
    ```
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            # Try to execute the function
            result = func(*args, **kwargs)

            # Success! Return immediately
            if attempt > 1:
                logger.info(f"[OK] Request succeeded after {attempt} attempts")
            return True, result

        except Exception as e:
            last_exception = e
            error_msg = str(e)

            # Check if error is retryable (transient failures only)
            # Retryable: 429 rate limit, 5xx server errors, timeouts, connection errors
            # Not retryable: 4xx client errors (bad request, auth, not found, etc.)
            is_retryable = (
                "429" in error_msg  # Rate limit exceeded (Too Many Requests)
                or "5" in error_msg[:1]  # 5xx server errors (500, 502, 503, 504)
                or "timeout" in error_msg.lower()  # Connection timeout
                or "connection" in error_msg.lower()  # Connection refused/reset
            )

            if not is_retryable or attempt >= max_attempts:
                # Either non-retryable error or exhausted all attempts
                logger.warning(
                    f"[X] Request failed after {attempt} attempts: {error_msg}"
                )
                return False, e

            # Log retry attempt with context
            logger.warning(
                f"[WARN] Attempt {attempt}/{max_attempts} failed: {error_msg}"
            )
            logger.info(f"[Pending] Retrying in {delay:.1f}s... (exponential backoff)")

            # Wait before retrying (exponential backoff)
            time.sleep(delay)

            # Double the delay for next retry, but cap at max_delay
            # Example: 1s → 2s → 4s → 8s → 16s → 32s (stops growing)
            delay = min(delay * 2, max_delay)

    # Should never reach here (loop returns in all cases), but safety fallback
    return False, last_exception
