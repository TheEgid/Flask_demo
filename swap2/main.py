import sys
import time

try:
    from .core.logger import logger
except ImportError:
    # Fallback для прямого запуска файла
    from core.logger import logger


def RUNNER_SECOND(params: dict) -> dict:
    """Основная логика модуля."""
    time.sleep(1)
    logger.info("SWAP2: Start processing...")
    return {
        "message": "Swap2 finished processing",
        "input_keys": list(params.keys()),
        "input_values": list(params.values()),
    }


def parse_cli_args(argv: list[str]) -> dict:
    """Парсинг аргументов CLI в словарь."""
    parsed = {}
    for arg in argv:
        if "=" in arg:
            key, value = arg.split("=", 1)
            parsed[key] = value
    return parsed


if __name__ == "__main__":
    manual_params = parse_cli_args(sys.argv[1:])

    print(f"Running standalone test with params: {manual_params}...")
    result = RUNNER_SECOND(manual_params)

    print("Execution finished. Result:")
    print(result)
