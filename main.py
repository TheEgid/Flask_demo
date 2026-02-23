from flask import Flask, jsonify # pyright: ignore[reportMissingImports]
import importlib

app = Flask(__name__)

# Функция для парсинга строки параметров "key=val,key2=val2"
def parse_value_string(value_str):
    params = {}
    if not value_str:
        return params
    # Разбиваем строку по запятым
    pairs = value_str.split(',')
    for pair in pairs:
        if '=' in pair:
            key, val = pair.split('=', 1)
            params[key.strip()] = val.strip()
    return params

@app.route('/run/<action>/<path:value>')
def run_action(action, value):
    # Безопасность: проверяем имя модуля (только буквы/цифры, чтобы не вышли из директории)
    if not action.isalnum():
        return jsonify({"error": "Invalid module name"}), 400

    module_name = f"{action}.main"

    try:
        # Динамический импорт модуля (например, swap1.main)
        mod = importlib.import_module(module_name)
    except ImportError as e:  # noqa: F841
        return jsonify({"error": f"Module '{action}' not found"}), 404

    # Преобразуем параметры в словарь
    params = parse_value_string(value)

    # Проверяем наличие точки входа 'run' в импортированном модуле
    if hasattr(mod, 'run'):
        try:
            # Вызываем функцию run(params) из модуля
            result = mod.run(params)
            return jsonify({"status": "success", "data": result})
        except Exception as e:
            return jsonify({"error": f"Execution error: {str(e)}"}), 500
    else:
        return jsonify({"error": f"Module '{action}' does not have a 'run' function"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

# C:\PLAYGROUND\demo-coopii/venv/Scripts/Activate.ps1
