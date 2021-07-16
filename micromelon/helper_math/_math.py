import random as _rand
import math as _math

__all__ = [
    "randint",
    "random",
    "isBetween",
    "constrain",
    "scale",
    "isPrime",
]


def _isNumber(x):
    return isinstance(x, (int, float))


def randint(low, high):
    """
    Alias to python's random.randint
    Generate random integers between two numbers

    Args:
      low (int): lower bound
      high (int): upper bound

    Raises:
      Exception if arguments are not both integers

    Returns:
      a pseudorandom integer between low and high inclusive
    """
    if not isinstance(low, int) or not isinstance(high, int):
        raise Exception("Both arguments to randint must be integers")
    return _rand.randint(low, high)


def random():
    """
    Alias to python's random.random

    Returns:
      a random floating point number (decimal fraction) between 0 and 1
    """
    return _rand.random()


def isBetween(x, low, high):
    """
    Check if a number is between or equal to two other numbers
    If the lower bound is greater than the upper bound they will be switched

    Args:
      x (number): the number to check
      low (number): lower bound
      high (number): upper bound

    Raises:
      Exception if any of the arguments aren't numbers

    Returns:
      true iff (if and only if) x is between low and high inclusive
    """
    if not _isNumber(x) or not _isNumber(low) or not _isNumber(high):
        raise Exception("All arguments to Math.isBetween must be numbers")

    l = low
    h = high
    if low > high:
        h = low
        l = high

    return x >= l and x <= h


def constrain(x, low, high):
    """
    Restrict a number to a range

    Args:
      x (number): the number to restrict
      low (number): lower bound
      high (number): upper bound

    Raises:
      Exception if any of the arguments aren't numbers

    Returns:
      x clamped to between low and high inclusive
    """
    if not _isNumber(x) or not _isNumber(low) or not _isNumber(high):
        raise Exception("All arguments to Math.constrain must be numbers")
    if high < low:
        temp = low
        low = high
        high = temp

    if x >= high:
        return high
    if x <= low:
        return low
    return x


def scale(x, xmin, xmax, newMin, newMax):
    """
    Scale a number from the range xmin - xmax to the range newMin - newMax
    Output is restricted to between newMin and newMax inclusive
    If newMin is greater than newMax or xmin is greater than xmax
    it will be treated and inversely proportional

    Args:
      x (number): the input to scale
      xmin (number): the current minimum for x
      xmax (number): the current maximum for x
      newMin (number): the minimum of the range to scale x to
      newMax (number): the maximum of the range to scale x to

    Raises:
      Exception if any of the arguments aren't numbers
      Exception if xmin equals xmax or newMin equals newMax

    Returns
      x scaled from the range xmin - xmax to the range newMin - newMax
    """
    if (
        not _isNumber(x)
        or not _isNumber(xmin)
        or not _isNumber(xmax)
        or not _isNumber(newMin)
        or not _isNumber(newMax)
    ):
        raise Exception("All arguments to scale must be numbers")
    
    if xmin == xmax or newMin == newMax:
        raise Exception("Min and max cannot be the same number in scale function")
    
    scaled = (((x - xmin) / (xmax - xmin)) * (newMax - newMin)) + newMin
    return constrain(scaled, newMin, newMax)


def isPrime(n):
    """
    Determine if a number is a prime number
    Simple primality test using the 6k +- 1 optimisation
    https://en.wikipedia.org/wiki/Primality_test

    Args:
      n (int): number to check

    Raises:
      Exception if n is not an integer

    Returns:
      True if n is prime.  False otherwise
    """
    if not isinstance(n, int):
        raise Exception("Argument to isPrime must be an integer")

    if n <= 1:
        return False
    elif n <= 3:
        return True
    elif n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    s = int(_math.sqrt(n)) + 1
    while i <= s:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
