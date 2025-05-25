# OPMAS Log Ingestor Component
# Listens for incoming syslog messages (UDP) and puts them on an internal queue.

import asyncio
import datetime
import logging
from typing import Tuple

# OPMAS Imports
from .config import get_config
from .logging_config import setup_logging
from .mq import publish_message

logger = logging.getLogger(__name__)


# Protocol for UDP handling
class SyslogUDPProtocol(asyncio.DatagramProtocol):
    """Handles incoming UDP syslog messages."""

    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport
        sockname = transport.get_extra_info("sockname")
        logger.info(f"UDP Syslog listener started on {sockname}")

    def datagram_received(self, data: bytes, addr: Tuple[str, int]):
        """Called when a datagram is received."""
        arrival_time = datetime.datetime.now(datetime.timezone.utc)
        source_ip = addr[0]
        source_port = addr[1]

        try:
            # Attempt to decode using common encodings
            # UTF-8 is standard, but some devices might send latin-1 or others
            try:
                message_str = data.decode("utf-8")
            except UnicodeDecodeError:
                logger.warning(
                    f"Decoding error with UTF-8 from {source_ip}:{source_port}, trying latin-1..."
                )
                message_str = data.decode("latin-1", errors="replace")  # Replace invalid chars

            logger.debug(f"Received message from {source_ip}:{source_port}: {message_str[:100]}...")

            # Prepare data for the queue
            # We'll pass the raw string and metadata. The parser will handle structure.
            log_data = {
                "raw_message": message_str,
                "source_ip": source_ip,
                "arrival_ts_utc": arrival_time.isoformat(),
            }

            # Put the data onto the internal queue
            try:
                self.queue.put_nowait(log_data)
            except asyncio.QueueFull:
                logger.warning(
                    f"Internal raw log queue is full! Discarding message from {source_ip}. Consider increasing queue size or parser performance."
                )

        except Exception as e:
            logger.error(
                f"Error processing datagram from {source_ip}:{source_port}: {e}", exc_info=True
            )

    def error_received(self, exc):
        """Called when a send or receive operation raises an OSError."""
        logger.error(f"UDP Listener Error: {exc}")

    def connection_lost(self, exc):
        """Called when the connection is lost or closed."""
        logger.warning(f"UDP Syslog listener connection lost/closed: {exc}")
        # Depending on the deployment, might want to attempt restart here


# Main function to start the listener
async def start_log_ingestor(log_queue: asyncio.Queue):
    """Starts the UDP Syslog listener server and puts messages on the queue."""
    # Ensure logging is configured (might be redundant)
    # setup_logging()
    config = get_config()
    ingestor_config = config.get("log_ingestor", {})
    listen_addr = ingestor_config.get("listen_address", "0.0.0.0")
    udp_port = ingestor_config.get("udp_port", 1514)  # Defaulting higher

    logger.info(f"Starting Log Ingestor UDP listener on {listen_addr}:{udp_port}...")

    loop = asyncio.get_running_loop()
    try:
        # Pass the log_queue to the protocol factory
        transport, protocol = await loop.create_datagram_endpoint(
            lambda: SyslogUDPProtocol(log_queue),  # Pass queue here
            local_addr=(listen_addr, udp_port),
        )

        # Keep the server running (replace with a more robust shutdown mechanism)
        await asyncio.Event().wait()  # Keep running indefinitely until interrupted

    except PermissionError:
        logger.error(
            f"Permission denied to bind to port {udp_port}. Try running as root or using a port > 1024."
        )
    except OSError as e:
        logger.error(f"OSError starting UDP listener on {listen_addr}:{udp_port}: {e}")
    except Exception as e:
        logger.error(f"Failed to start Log Ingestor: {e}", exc_info=True)
    finally:
        if "transport" in locals() and transport:
            logger.info("Closing UDP transport...")
            transport.close()


# Example of how another component (like the parser) might consume from the queue
async def consume_logs_example():
    """Demonstrates consuming logs from the internal queue."""
    logger.info("Log consumer starting...")
    while True:
        try:
            log_data = await raw_log_queue.get()
            logger.info(f"Consumed log: {log_data}")
            # --- In reality, pass log_data to the Log Parser here ---
            raw_log_queue.task_done()  # Notify queue that item processing is complete
            await asyncio.sleep(0.1)  # Simulate processing time
        except asyncio.CancelledError:
            logger.info("Log consumer shutting down.")
            break
        except Exception as e:
            logger.error(f"Error in log consumer: {e}", exc_info=True)
            await asyncio.sleep(1)  # Avoid tight loop on error


if __name__ == "__main__":
    # Setup logging and config first
    setup_logging()
    get_config()  # Load config

    async def main():
        logger.info("Starting OPMAS Log Ingestor Service (and example consumer)...")
        ingestor_task = asyncio.create_task(start_log_ingestor())
        consumer_task = asyncio.create_task(consume_logs_example())  # Run example consumer

        # Wait for tasks (or handle shutdown signals)
        done, pending = await asyncio.wait(
            [ingestor_task, consumer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()
        await asyncio.gather(
            *pending, return_exceptions=True
        )  # Allow pending tasks to finish cancelling
        logger.info("Log Ingestor service stopped.")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user.")
