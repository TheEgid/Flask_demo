import sys


def RUNNER_FIRST(params: dict) -> dict:
    """
    Эта функция вызывается Flask.
    params -- словарь с параметрами из URL.
    """
    # Пример логики
    name = params.get('name', 'Unknown')
    count = params.get('count', 0)

    # Возвращаем результат (Flask превратит это в JSON)
    return {
        "message": f"Swap1 executed for {name} with count {count}",
        "received_params": params
    }


# Этот блок выполняется ТОЛЬКО при прямом запуске:
# python swap1/main.py key=value ...
if __name__ == '__main__':
    # Простая имитация парсинга параметров из командной строки
    # Пример запуска: python main.py name=Ivan count=5
    input_params = {}

    # Перебираем аргументы командной строки
    for arg in sys.argv[1:]:
        if '=' in arg:
            key, value = arg.split('=', 1)
            input_params[key] = value

    print(f"Direct run with params: {input_params}")

    # Вызываем функцию run
    result = RUNNER_FIRST(input_params)
    print("Result:", result)
