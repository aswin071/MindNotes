"""
MongoDB utility functions with retry logic and connection handling
"""
import functools
import time
import logging
from typing import Callable, Any
from pymongo.errors import AutoReconnect, ConnectionFailure, ServerSelectionTimeoutError
from core.exceptions import DatabaseConnectionException

logger = logging.getLogger(__name__)


def retry_on_db_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry MongoDB operations on connection failures

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry

    Usage:
        @retry_on_db_error(max_retries=3, delay=1.0, backoff=2.0)
        def my_mongo_operation():
            # Your MongoDB operation here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except (AutoReconnect, ConnectionFailure, ServerSelectionTimeoutError) as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"MongoDB operation '{func.__name__}' failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"MongoDB operation '{func.__name__}' failed after {max_retries + 1} attempts: {str(e)}"
                        )

                except Exception as e:
                    # Don't retry on other exceptions
                    logger.error(f"MongoDB operation '{func.__name__}' failed with non-retryable error: {str(e)}")
                    raise

            # If we've exhausted all retries, raise the last exception wrapped in our custom exception
            raise DatabaseConnectionException(
                database="MongoDB",
                message=f"Failed after {max_retries + 1} attempts: {str(last_exception)}"
            )

        return wrapper
    return decorator


def safe_mongo_operation(func: Callable, fallback_value: Any = None, log_errors: bool = True) -> Callable:
    """
    Decorator to safely execute MongoDB operations with fallback

    Args:
        func: Function to wrap
        fallback_value: Value to return if operation fails
        log_errors: Whether to log errors

    Usage:
        @safe_mongo_operation
        def get_user_data(user_id):
            # Your MongoDB operation
            return data
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                logger.error(f"Safe MongoDB operation '{func.__name__}' failed: {str(e)}")
            return fallback_value

    return wrapper


class MongoConnectionPool:
    """
    MongoDB connection pool manager with health checks
    """

    @staticmethod
    def check_connection():
        """Check if MongoDB connection is healthy"""
        try:
            import mongoengine
            mongoengine.connection.get_db().command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB connection check failed: {str(e)}")
            return False

    @staticmethod
    def reconnect():
        """Attempt to reconnect to MongoDB"""
        try:
            import mongoengine
            from django.conf import settings

            # Disconnect existing connections
            mongoengine.disconnect()

            # Reconnect
            mongoengine.connect(
                db=settings.MONGODB_DB_NAME,
                **settings.MONGODB_CONNECTION,
                maxPoolSize=50,
                minPoolSize=10,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=10000,
                retryWrites=True,
                w='majority',
                alias='default',
                uuidRepresentation='standard',
                tls=True,
                tlsInsecure=True
            )

            logger.info("MongoDB reconnection successful")
            return True

        except Exception as e:
            logger.error(f"MongoDB reconnection failed: {str(e)}")
            return False


# Pre-configured decorators for common use cases
retry_db_operation = retry_on_db_error(max_retries=3, delay=1.0, backoff=2.0)
retry_critical_operation = retry_on_db_error(max_retries=5, delay=0.5, backoff=1.5)
