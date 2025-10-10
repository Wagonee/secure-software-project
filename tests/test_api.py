from http import HTTPStatus

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_health():
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "Welcome to Workout Log API!"}


def test_create_exercise():
    response = client.post(
        "/exercises/",
        json={
            "name": "Приседания со штангой",
            "description": "Базовое упражнение на ноги",
        },
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["name"] == "Приседания со штангой"
    assert "id" in data


def test_get_all_exercises():
    client.post("/exercises/", json={"name": "Жим лежа"})

    response = client.get("/exercises/")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert isinstance(data, list)

    assert any(ex["name"] == "Жим лежа" for ex in data)


def test_create_workout():
    response = client.post(
        "/workouts/",
        json={"workout_date": "2025-09-25", "note": "День ног"},
    )
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["workout_date"] == "2025-09-25"
    assert data["note"] == "День ног"
    assert "id" in data
    assert "sets" in data and isinstance(data["sets"], list)


def test_get_workout_by_id():
    create_response = client.post("/workouts/", json={"workout_date": "2025-09-26"})
    workout_id = create_response.json()["id"]

    get_response = client.get(f"/workouts/{workout_id}")
    assert get_response.status_code == HTTPStatus.OK
    data = get_response.json()
    assert data["id"] == workout_id
    assert data["workout_date"] == "2025-09-26"


def test_get_workout_not_found():
    random_uuid = "a1b2c3d4-e5f6-7890-1234-567890abcdef"
    response = client.get(f"/workouts/{random_uuid}")
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_add_set_to_workout():
    exercise_res = client.post("/exercises/", json={"name": "Подтягивания"})
    exercise_id = exercise_res.json()["id"]

    workout_res = client.post(
        "/workouts/", json={"workout_date": "2025-09-27", "note": "День спины"}
    )
    workout_id = workout_res.json()["id"]

    set_data = {"reps": 10, "weight": 80.0}
    response = client.post(
        f"/workouts/{workout_id}/sets?exercise_id={exercise_id}",
        json=set_data,
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["sets"]) == 1
    added_set = data["sets"][0]
    assert added_set["exercise_name"] == "Подтягивания"
    assert added_set["reps"] == 10
    assert added_set["weight"] == 80.0
    assert "id" in added_set


def test_rate_limiting():
    # Отправляем много запросов подряд
    responses = []
    for _ in range(105):  # Чуть больше лимита
        response = client.post("/workouts/", 
                             json={"workout_date": "2025-09-25"})
        responses.append(response.status_code)
    
    # Проверяем, что есть 429 (Too Many Requests)
    assert 429 in responses

def test_rate_limiting():
    responses = []
    for _ in range(105):
        response = client.post("/workouts/", 
                             json={"workout_date": "2025-09-25"})
        responses.append(response.status_code)    
    assert 429 in responses