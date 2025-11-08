"""
Input validation tests and negative scenarios.
Tests strict field constraints, boundary conditions, and rejection of invalid data.
"""

import os
from http import HTTPStatus
from importlib import import_module
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path: Path):
    """Creates unique test client with isolated DB for each test"""
    test_db = tmp_path / f"test_validation_{id(tmp_path)}.db"
    if test_db.exists():
        try:
            test_db.unlink()
        except OSError:
            pass  # noqa: S110 - Expected in test cleanup

    os.environ["DATABASE_URL"] = f"sqlite:///{test_db.as_posix()}"
    app = import_module("app.main").app
    import sys

    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    app = import_module("app.main").app
    with TestClient(app) as c:
        yield c


def test_negative_reps_rejected(client):
    """Test: reject negative reps"""
    exercise_res = client.post("/exercises/", json={"name": "Test Exercise"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": -5, "weight": "50.0"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "correlation_id" in data
    assert data["title"] == "Validation Error"


def test_zero_reps_rejected(client):
    """Тест: отклонение нулевого количества повторений"""
    exercise_res = client.post("/exercises/", json={"name": "Test Exercise"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 0, "weight": "50.0"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_excessive_reps_rejected(client):
    """Тест: отклонение слишком большого количества повторений (>1000)"""
    exercise_res = client.post("/exercises/", json={"name": "Test Exercise"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 1001, "weight": "50.0"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_negative_weight_rejected(client):
    """Тест: отклонение отрицательного веса"""
    exercise_res = client.post("/exercises/", json={"name": "Test Exercise"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 10, "weight": "-10.5"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_weight_precision_validation(client):
    """Тест: проверка точности веса (max 2 знака после запятой)"""
    exercise_res = client.post("/exercises/", json={"name": "Test Exercise"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    # Допустимая точность
    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 10, "weight": "100.25"},
    )
    assert response.status_code == HTTPStatus.OK

    # Слишком много знаков после запятой - должно быть отклонено
    response2 = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 10, "weight": "100.256"},
    )
    assert response2.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_exercise_name_too_long_rejected(client):
    """Тест: отклонение слишком длинного названия упражнения"""
    long_name = "A" * 201  # Больше max_length=200
    response = client.post("/exercises/", json={"name": long_name})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    data = response.json()
    assert "correlation_id" in data


def test_exercise_name_empty_rejected(client):
    """Тест: отклонение пустого названия упражнения"""
    response = client.post("/exercises/", json={"name": ""})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_exercise_name_with_control_characters_rejected(client):
    """Тест: отклонение названия с управляющими символами"""
    response = client.post("/exercises/", json={"name": "Test\x00Exercise"})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_workout_note_too_long_rejected(client):
    """Тест: отклонение слишком длинной заметки тренировки"""
    long_note = "X" * 1001  # Больше max_length=1000
    response = client.post("/workouts/", json={"workout_date": "2025-11-08", "note": long_note})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_workout_note_sanitization(client):
    """Тест: санитизация заметки - удаление управляющих символов"""
    note_with_control = "Normal text\x00\x01\x02cleaned"
    response = client.post(
        "/workouts/", json={"workout_date": "2025-11-08", "note": note_with_control}
    )
    # Должно пройти валидацию, но управляющие символы должны быть удалены
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    # Проверяем что управляющие символы не сохранились
    assert "\x00" not in data.get("note", "")


def test_invalid_date_format_rejected(client):
    """Тест: отклонение некорректного формата даты"""
    response = client.post("/workouts/", json={"workout_date": "not-a-date", "note": "Test"})
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_correlation_id_in_all_errors(client):
    """Тест: наличие correlation_id во всех типах ошибок"""
    # 404 ошибка
    response1 = client.get("/workouts/00000000-0000-0000-0000-000000000000")
    assert response1.status_code == HTTPStatus.NOT_FOUND
    assert "correlation_id" in response1.json()

    # Validation ошибка
    response2 = client.post("/exercises/", json={"name": ""})
    assert response2.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
    assert "correlation_id" in response2.json()

    # Rate limit ошибка (нужно много запросов)
    # Проверяем формат ответа
    response3 = client.get("/health")
    # Проверяем что есть correlation_id в заголовке
    assert "X-Correlation-ID" in response3.headers


def test_decimal_weight_storage_and_retrieval(client):
    """Тест: корректное хранение и извлечение Decimal значений для веса"""
    exercise_res = client.post("/exercises/", json={"name": "Bench Press"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post("/workouts/", json={"workout_date": "2025-11-08"})
    workout_id = workout_res.json()["id"]

    # Добавляем подход с точным весом
    set_response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json={"reps": 10, "weight": "82.50"},
    )
    assert set_response.status_code == HTTPStatus.OK

    # Получаем тренировку и проверяем точность
    get_response = client.get(f"/workouts/{workout_id}")
    assert get_response.status_code == HTTPStatus.OK
    data = get_response.json()
    assert len(data["sets"]) == 1
    # Вес должен сохраниться точно
    stored_weight = data["sets"][0]["weight"]
    assert str(stored_weight) == "82.50" or float(stored_weight) == 82.50


def test_rfc7807_error_structure(client):
    """Тест: проверка полной структуры RFC 7807 ошибки"""
    response = client.get("/workouts/invalid-uuid-format")
    data = response.json()

    # Проверяем обязательные поля RFC 7807
    assert "type" in data
    assert "title" in data
    assert "status" in data
    assert "detail" in data
    assert "correlation_id" in data

    # Проверяем типы полей
    assert isinstance(data["status"], int)
    assert isinstance(data["correlation_id"], str)
