import sys
import time


def RUNNER_SECOND(params: dict) -> dict:
    """Основная логика модуля."""
    time.sleep(1)  # Имитация долгой работы
    return {
        "message": "Swap2 finished processing",
        "input_keys": list(params.keys()),
        "input_values": list(params.values())
    }


# Этот код выполнится только при прямом запуске файла
if __name__ == '__main__':
    # Пример запуска: python main.py id=123 status=active

    # Парсинг аргументов командной строки в словарь
    manual_params = {}
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            manual_params[key] = value

    print(f"Running standalone test with params: {manual_params}...")

    # Вызов основной функции
    result = RUNNER_SECOND(manual_params)

    print("Execution finished. Result:")
    print(result)
