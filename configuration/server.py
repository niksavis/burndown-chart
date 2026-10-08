import argparse
import os

from configuration.settings import logger

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8050
DEFAULT_SERVER_MODE = "production"


def get_server_config():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode with Flask development server",
    )
    parser.add_argument(
        "--prod", action="store_true", help="Run in production mode with Waitress"
    )
    parser.add_argument("--host", type=str, help="Host address to bind the server to")
    parser.add_argument("--port", type=int, help="Port to run the server on")
    args, _ = parser.parse_known_args()

    server_mode = DEFAULT_SERVER_MODE

    if args.debug:
        server_mode = "debug"
    elif args.prod:
        server_mode = "production"
    elif os.environ.get("BURNDOWN_SERVER_MODE", "").lower() in ("debug", "production"):
        server_mode = os.environ.get("BURNDOWN_SERVER_MODE").lower()

    host = args.host or os.environ.get("BURNDOWN_HOST", DEFAULT_HOST)

    try:
        port = args.port or int(os.environ.get("BURNDOWN_PORT", DEFAULT_PORT))
    except ValueError, TypeError:
        logger.warning(f"Invalid port specified, using default: {DEFAULT_PORT}")
        port = DEFAULT_PORT

    config = {
        "mode": server_mode,
        "debug": server_mode == "debug",
        "host": host,
        "port": port,
    }

    logger.info(f"Server configuration: {config}")
    return config
