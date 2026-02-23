import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import main
from main import ALLOWED_ACTIONS, app


@pytest.fixture
def client():
    """Создаём тестовый клиент Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestMainRoutes:
    """Тесты основных маршрутов."""

    def test_swap1_success(self, client):
        """Тест успешного выполнения swap1."""
        response = client.get('/run/swap1?name=Test&count=5')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'success'
        assert 'Swap1 executed for Test with count 5' in data['data']['message']
        assert data['data']['received_params'] == {'name': 'Test', 'count': '5'}

    def test_swap1_no_params(self, client):
        """Тест swap1 без параметров (должны использоваться значения по умолчанию)."""
        response = client.get('/run/swap1')
        assert response.status_code == 200

        data = response.get_json()
        assert 'Unknown' in data['data']['message']
        assert '0' in data['data']['message']

    def test_swap2_success(self, client):
        """Тест успешного выполнения swap2."""
        response = client.get('/run/swap2?id=123&status=active')
        assert response.status_code == 200

        data = response.get_json()
        assert data['status'] == 'success'
        assert data['data']['message'] == 'Swap2 finished processing'
        assert data['data']['input_keys'] == ['id', 'status']
        assert data['data']['input_values'] == ['123', 'active']

    def test_swap2_delay_simulation(self, client):
        """Тест что swap2 действительно выполняется (с задержкой)."""
        import time
        start = time.time()
        response = client.get('/run/swap2')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed >= 0.9  # Проверяем задержку ~1 секунда

    def test_forbidden_action(self, client):
        """Тест запрещённого действия."""
        response = client.get('/run/swap3')
        assert response.status_code == 403

        data = response.get_json()
        assert 'error' in data
        assert 'not allowed' in data['error']

    def test_module_not_found(self, client):
        """Тест когда модуль не существует (но действие в ALLOWED_ACTIONS)."""
        # Временно добавляем несуществующий модуль в разрешённые
        original_actions = ALLOWED_ACTIONS.copy()
        ALLOWED_ACTIONS['nonexistent'] = 'RUNNER_FUNC'

        try:
            response = client.get('/run/nonexistent')
            assert response.status_code == 404
            data = response.get_json()
            assert 'Module not found' in data['error']
        finally:
            ALLOWED_ACTIONS.clear()
            ALLOWED_ACTIONS.update(original_actions)


class TestModuleFunctions:
    """Тесты функций модулей напрямую."""

    def test_runner_first_direct(self):
        """Тест RUNNER_FIRST напрямую."""
        from swap1.main import RUNNER_FIRST

        result = RUNNER_FIRST({'name': 'Direct', 'count': '10'})
        assert 'Direct' in result['message']
        assert '10' in result['message']
        assert result['received_params'] == {'name': 'Direct', 'count': '10'}

    def test_runner_second_direct(self):
        """Тест RUNNER_SECOND напрямую."""
        import time

        from swap2.main import RUNNER_SECOND

        start = time.time()
        result = RUNNER_SECOND({'key': 'value'})
        elapsed = time.time() - start

        assert elapsed >= 0.9
        assert result['message'] == 'Swap2 finished processing'
        assert result['input_keys'] == ['key']
        assert result['input_values'] == ['value']

    def test_request_logging(self, client):
        """Тест что запросы логируются."""

        # Подменяем логгер на мок
        original_logger = main.main_logger
        mock_logger = MagicMock()
        main.main_logger = mock_logger

        try:
            client.get('/run/swap1?name=LogTest')

            # Проверяем вызовы
            info_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any('swap1' in str(call) for call in info_calls)
            assert any('LogTest' in str(call) for call in info_calls)
        finally:
            main.main_logger = original_logger


@pytest.fixture
def project_root():
    """Возвращает путь к корню проекта."""
    return Path(__file__).parent.parent


class TestCLI:
    """Тесты командной строки модулей."""

    def test_swap1_cli(self, project_root, monkeypatch):
        """Тест запуска swap1 из командной строки."""
        import subprocess

        monkeypatch.chdir(project_root)

        result = subprocess.run(
            [sys.executable, 'swap1/main.py', 'name=CLI', 'count=99'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Stderr: {result.stderr}"
        assert 'CLI' in result.stdout
        assert '99' in result.stdout

    def test_swap2_cli(self, project_root, monkeypatch):
        """Тест запуска swap2 из командной строки."""
        import subprocess

        monkeypatch.chdir(project_root)

        result = subprocess.run(
            [sys.executable, 'swap2/main.py', 'id=CLI', 'status=testing'],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Stderr: {result.stderr}"
        assert 'finished processing' in result.stdout
        assert 'CLI' in result.stdout


# Для запуска тестов напрямую
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
