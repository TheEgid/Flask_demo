import importlib
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, jsonify, request


def setup_logger(name: str = "app_logger") -> logging.Logger:
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-5.5s| %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    # --- 1. Консольный обработчик ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)

    # --- 2. Файловый обработчик ---
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


# Инициализируем
main_logger = setup_logger()


ALLOWED_ACTIONS = {
    "swap1": "RUNNER_FIRST",
    "swap2": "RUNNER_SECOND"
}


app = Flask(__name__)


@app.route('/run/<action>')
def run_action(action: str) -> jsonify:
    # Логируем начало запроса
    main_logger.info(f"Запрос на действие: {action} | IP: {request.remote_addr}")

    func_name = ALLOWED_ACTIONS.get(action)
    if not func_name:
        main_logger.warning(f"Попытка доступа к запрещенному или отсутствующему действию: {action}")
        return jsonify({"error": f"Action '{action}' is not allowed"}), 403

    params = request.args.to_dict()
    main_logger.info(f"Параметры запроса: {params}")

    module_name = f"{action}.main"

    try:
        mod = importlib.import_module(module_name)

        if hasattr(mod, func_name):
            runner_func = getattr(mod, func_name)

            main_logger.info(f"Запуск функции {func_name} из модуля {module_name}...")
            result = runner_func(params)

            main_logger.info(f"Действие {action} успешно завершено.")
            return jsonify({"status": "success", "data": result})

        else:
            main_logger.error(f"В модуле {module_name} отсутствует функция {func_name}")
            return jsonify({"error": "Entry point missing"}), 500

    except ImportError:
        main_logger.error(f"Не удалось импортировать модуль {module_name}")
        return jsonify({"error": "Module not found"}), 404
    except Exception as e:
        main_logger.exception(f"Критическая ошибка при выполнении {action}: {e!s}")
        return jsonify({"error": "Internal execution error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
