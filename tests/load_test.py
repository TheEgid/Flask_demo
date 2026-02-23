import concurrent.futures
import platform
import statistics
import time

import pytest
import requests

BASE_URL = "http://localhost:5000" if platform.system() == 'Windows' else "http://localhost:80"


def make_request(endpoint, params=""):
    """Выполняет один запрос и возвращает время выполнения."""
    url = f"{BASE_URL}/run/{endpoint}"
    if params:
        url += f"?{params}"

    start = time.time()
    try:
        response = requests.get(url, timeout=10)
        elapsed = time.time() - start
        return {
            'status_code': response.status_code,
            'elapsed': elapsed,
            'success': response.status_code == 200
        }
    except Exception as e:
        return {
            'status_code': 0,
            'elapsed': time.time() - start,
            'success': False,
            'error': str(e)
        }


def load_test(endpoint, params="", num_requests=10, concurrency=2, delay=0.5):
    """Проводит нагрузочное тестирование с низкой интенсивностью."""
    print(f"\n{'=' * 50}")
    print(f"Нагрузочный тест: {endpoint}")
    print(f"Параметры: {params or 'нет'}")
    print(f"Запросов: {num_requests}, Параллельность: {concurrency}, Задержка: {delay}s")
    print(f"{'=' * 50}")

    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = []
        for i in range(num_requests):
            if i > 0:
                time.sleep(delay)
            futures.append(executor.submit(make_request, endpoint, params))

        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    times = [r['elapsed'] for r in successful]

    print("\nРезультаты:")
    print(f"  Успешно: {len(successful)}/{num_requests}")
    print(f"  Ошибки: {len(failed)}")

    if times:
        print("\nВремя отклика (сек):")
        print(f"  Минимальное: {min(times):.3f}")
        print(f"  Максимальное: {max(times):.3f}")
        print(f"  Среднее: {statistics.mean(times):.3f}")
        print(f"  Медиана: {statistics.median(times):.3f}")
        if len(times) > 1:
            print(f"  Стд. отклонение: {statistics.stdev(times):.3f}")

    if failed:
        print("\nОшибки:")
        for f in failed[:5]:
            print(f"  {f.get('error', 'Unknown error')}")

    return {
        'endpoint': endpoint,
        'total': num_requests,
        'success': len(successful),
        'failed': len(failed),
        'times': times
    }


@pytest.fixture(scope="module")
def check_server():
    """Проверяет доступность сервера перед тестами."""
    try:
        requests.get(f"{BASE_URL}/run/swap1", timeout=2)
    except requests.ConnectionError:
        pytest.skip("Flask-сервер не запущен на localhost:5000")


class TestLoad:
    """Нагрузочные тесты."""

    @pytest.mark.parametrize("endpoint,params,requests,concurrency,delay", [
        ("swap1", "name=LoadTest&count=1", 5, 2, 1.0),
        ("swap2", "id=load&status=test", 3, 1, 2.0),
    ])
    def test_load_endpoint(self, check_server, endpoint, params, requests, concurrency, delay):
        """Тест нагрузки для разных endpoint."""
        result = load_test(endpoint, params, requests, concurrency, delay)

        assert result['failed'] == 0, f"Есть ошибки: {result['failed']}"
        assert result['success'] == result['total'], "Не все запросы успешны"

        if result['times']:
            avg_time = statistics.mean(result['times'])
            assert avg_time < 5.0, f"Среднее время отклика слишком высокое: {avg_time:.3f}s"

    def test_swap1_light_load(self, check_server):
        """Лёгкая нагрузка на swap1."""
        result = load_test("swap1", "name=test", num_requests=3, concurrency=1, delay=0.5)
        assert result['success'] >= 2

    def test_swap2_single_request(self, check_server):
        """Одиночный запрос к swap2 (с sleep)."""
        result = load_test("swap2", "id=single", num_requests=1, concurrency=1, delay=0)
        assert result['success'] == 1
        assert result['times'][0] >= 0.9
