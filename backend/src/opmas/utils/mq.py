import asyncio
import nats
from nats.errors import ConnectionClosedError, TimeoutError, NoServersError
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
NATS_URL = "nats://localhost:4222"

# Module-level shared client for components that don't manage their own
_shared_nats_client = None

def _reset_shared_client():
    """Helper function to reset the global shared client variable."""
    global _shared_nats_client
    logger.warning("Resetting shared NATS client variable.")
    _shared_nats_client = None

async def get_shared_nats_client():
    """Gets the shared NATS client, creating it if necessary."""
    global _shared_nats_client
    if _shared_nats_client is None or not _shared_nats_client.is_connected:
        try:
            _shared_nats_client = await nats.connect(NATS_URL, name="opmas_shared_publisher")
            logger.info(f"Created shared NATS client connected to {NATS_URL}...")
        except NoServersError as e:
            logger.error(f"Could not connect shared client to any NATS server: {e}")
            _shared_nats_client = None # Ensure it's None if connection failed
            raise # Re-raise the exception
        except Exception as e:
            logger.error(f"Error creating shared NATS client: {e}", exc_info=True)
            _shared_nats_client = None
            raise
    return _shared_nats_client

async def publish_message(subject: str, message_dict: dict, nats_client: Optional[nats.NATS] = None):
    """Publishes a dictionary as a JSON message to a NATS subject."""
    nc = nats_client or await get_shared_nats_client() # Use provided client or the singleton
    if not nc or not nc.is_connected:
        logger.error(f"Cannot publish to {subject}: NATS client not connected.")
        return

    try:
        payload = json.dumps(message_dict).encode('utf-8')
        # print(f"DEBUG: MQ: Attempting nc.publish to {subject}", flush=True)
        await nc.publish(subject, payload)
        # print(f"DEBUG: MQ: nc.publish call completed for {subject}", flush=True)
        # logger.debug(f"Published message to {subject}: {message_dict}") # Avoid logging potentially large dicts at debug
        logger.info(f"Published message to {subject}") # Log only subject on INFO

    except NoServersError as e:
        global _shared_nats_client
        logger.error(f"NATS NoServersError during publish: {e}")
        _reset_shared_client()
    except ConnectionClosedError:
        global _shared_nats_client
        logger.error("NATS ConnectionClosedError during publish.")
        _reset_shared_client()
    except TimeoutError:
        logger.error(f"Timeout occurred while publishing message to '{subject}'.")
    except Exception as e:
        logger.error(f"An error occurred during NATS publish to '{subject}': {e}", exc_info=True)
    # *** REMOVED finally block that closed the connection ***


async def subscribe_handler(subject: str, callback: callable, nats_client=None, queue=""):
    """Connects to NATS (if no client provided) and subscribes to a subject, calling the callback for each message."""
    # *** IMPORTANT: This function still creates a connection per subscriber if no client is passed.
    # *** This is generally okay for long-running components like agents/orchestrator/executor
    # *** as they pass their own client. If used elsewhere without a client, it might be inefficient.
    nc = nats_client
    should_close_on_error = False # Flag to track if we created the client
    try:
        if nc is None:
            # Create a persistent client for this specific subscription handler instance
            subscriber_name = f"subscriber_{subject.replace('.', '_')}_{queue or 'default'}"
            nc = await nats.connect(NATS_URL, name=subscriber_name)
            should_close_on_error = True # We are responsible for this client
            logger.info(f"Connected to NATS at {NATS_URL} for subscription to '{subject}'...")

        elif not nc.is_connected:
             # If an external client is passed and it's not connected, we cannot proceed.
             logger.error(f"Provided NATS client for subject '{subject}' is not connected.")
             return None, None # Indicate failure

        async def message_handler(msg):
            msg_subject = msg.subject
            data_str = msg.data.decode()
            logger.debug(f"Received message on subject '{msg_subject}': {data_str[:100]}...") # Log truncated data
            try:
                data_dict = json.loads(data_str)
                # Ensure the callback is awaited if it's a coroutine
                result = callback(data_dict)
                if asyncio.iscoroutine(result):
                    await result
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from message on subject '{msg_subject}': {data_str}")
            except Exception as e:
                logger.error(f"Error processing message from subject '{msg_subject}': {e}", exc_info=True)

        # Use queue groups for load balancing if queue name is provided
        sub = await nc.subscribe(subject, queue=queue, cb=message_handler)
        logger.info(f"Subscribed to '{subject}' with queue '{queue}'")

        # Return the client (whether passed in or created) and the subscription object
        # The caller is responsible for managing the client's lifecycle if it was passed in.
        # If we created the client (should_close_on_error is True), ideally the caller
        # would store nc and close it on graceful shutdown. This utility doesn't enforce that.
        return nc, sub

    except NoServersError as e:
        logger.error(f"Could not connect to any NATS server for subscription to '{subject}': {e}")
        if should_close_on_error and nc and nc.is_connected:
            await nc.close() # Clean up the client we created
        return None, None
    except Exception as e:
        logger.error(f"An error occurred during NATS subscription setup for '{subject}': {e}", exc_info=True)
        if should_close_on_error and nc and nc.is_connected:
             await nc.close() # Clean up the client we created
        return None, None

# Example usage remains the same, but demonstrates how subscribe_handler returns the client
# Note: The original example usage's cleanup logic needs adjustment if relying on the new shared publisher.
# The example main() is less relevant now as the core logic is used by other modules.
# if __name__ == '__main__':
#     try:
#         asyncio.run(main())
#     except KeyboardInterrupt:
#         print("Interrupted by user.") 