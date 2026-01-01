from unittest.mock import patch, AsyncMock
import httpx
import pytest

def add_course_payload(course_id = "1234", course_name = "Robotics", description = "Autonomous drones", enrolled_users = []):
    return {"course_id": course_id, "course_name": course_name, "description": description, "enrolled_users": enrolled_users}

def get_course_payload(course_id = "1234", course_name = "Robotics", description = "Autonomous drones", id = 1, enrolled_users = []):
    return {"course_id": course_id, "course_name": course_name, "description": description, "id": id, "enrolled_users": enrolled_users}
####################################################################################

def test_add_course_ok(client):
    r = client.post("/api/add-course", json = add_course_payload())
    assert r.status_code == 201
    assert r.json() == get_course_payload()

def test_add_course_invalid_course_id(client):
    r = client.post("/api/add-course", json = {"course_id": "1", "course_name": "Robotics", "description": "Drones"})
    assert r.status_code == 422

def test_add_course_invalid_course_name(client):
    r = client.post("/api/add-course", json = {"course_id": "1234", "course_name": "R", "description": "Drones"})
    assert r.status_code == 422

def test_add_course_invalid_description(client):
    r = client.post("/api/add-course", json = {"course_id": "1234", "course_name": "Robotics", "description": "D" * 3000})
    assert r.status_code == 422

def test_get_all_courses_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    client.post("/api/add-course", json = add_course_payload(course_id="5678", course_name="ML", description="AI"))
    r = client.get("/api/get-all-courses")
    assert r.status_code == 200
    assert r.json() == [get_course_payload(), get_course_payload(course_id="5678", course_name="ML", description="AI", id=2)]

def test_get_all_courses_empty(client):
    r = client.get("/api/get-all-courses")
    assert r.status_code == 200
    assert r.json() == []

def test_get_course_by_id_ok(client):
    client.post("/api/add-course", json=add_course_payload())
    r = client.get("/api/get-course-by-id/1234")
    assert r.status_code == 200
    assert r.json() == get_course_payload()

def test_get_course_by_id_not_found(client):
    r = client.get("/api/get-course-by-id/9999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Course not found"}

def test_get_course_by_user_id_ok(client):
    client.post("/api/add-course", json=add_course_payload())
    client.post("/api/courses/1234/enroll/g00425075")
    r = client.get("/api/course-by-user-id/g00425075")
    assert r.status_code == 200
    assert r.json() == get_course_payload(enrolled_users=["g00425075"])

def test_get_course_by_user_id_not_found(client):
    client.post("/api/add-course", json=add_course_payload())
    client.post("/api/courses/1234/enroll/g00425075")
    r = client.get("/api/course-by-user-id/g00425076")
    assert r.status_code == 404
    assert r.json() == {"detail": "Course not found for the specific user"}

def test_update_course_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.put("/api/update-course-by-id/1234", json = {"course_name": "CICD", "description": "CICDIDDY"})
    assert r.status_code == 200
    assert r.json() == {"message": "Course updated successful"}

def test_update_course_not_found(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.put("/api/update-course-by-id/5678", json = {"course_name": "CICD", "description": "CICDIDDY"})
    assert r.status_code == 404
    assert r.json() == {"detail": "id not found"}

def test_patch_course_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.patch("/api/patch-course-by-id/1234", json = {"course_name": "CICD2"})
    assert r.status_code == 200
    assert r.json() == {"message": "Course patched successful"}

def test_patch_course_not_found(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.patch("/api/patch-course-by-id/5678", json = {"course_name": "CICD2"})
    assert r.status_code == 404
    assert r.json() == {"detail": "Course ID not found"}

def test_delete_course_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.delete("/api/delete-course-by-id/1234")
    assert r.status_code == 200
    assert r.json() == {"message": "Deleted Course"}

def test_delete_course_not_found(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.delete("/api/delete-course-by-id/5678")
    assert r.status_code == 404
    assert r.json() == {"detail": "course_id not found for delete"}

def test_enroll_user_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.post("/api/courses/1234/enroll/g00425075")
    assert r.status_code == 200
    assert r.json() == {"message": "User g00425075 enrolled in course 1234"}

def test_enroll_user_course_not_found(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.post("/api/courses/2345/enroll/g00425075")
    assert r.status_code == 404
    assert r.json() == {"detail": "Course not found"}

def test_enroll_user_course_already_enrolled(client):
    client.post("/api/add-course", json = add_course_payload())
    client.post("/api/courses/1234/enroll/g00425075")
    r = client.post("/api/courses/1234/enroll/g00425075")
    assert r.status_code == 409
    assert r.json() == {"detail": "User already enrolled in course"}

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_get_course_by_db_id_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.get("/api/get-course-by-db-id/1")
    assert r.status_code == 200
    assert r.json() == get_course_payload()

def test_get_course_by_db_id_not_found(client):
    r = client.get("/api/get-course-by-db-id/999")
    assert r.status_code == 404
    assert r.json() == {"detail": "Course not found"}

def test_unenroll_user_ok(client):
    client.post("/api/add-course", json = add_course_payload())
    client.post("/api/courses/1234/enroll/g00425075")
    r = client.post("/api/courses/1234/unenroll/g00425075")
    assert r.status_code == 200
    assert r.json() == {"message": "User g00425075 unenrolled from course 1234"}

def test_unenroll_user_not_enrolled(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.post("/api/courses/1234/unenroll/g00425075")
    assert r.status_code == 200
    assert r.json() == {"message": "User was not enrolled"}

def test_unenroll_user_course_not_found(client):
    r = client.post("/api/courses/9999/unenroll/g00425075")
    assert r.status_code == 404
    assert r.json() == {"detail": "Course not found"}

def test_proxy_modules_ok(client):
    mock_response = httpx.Response(200, json=[{"id": 1, "name": "Module 1"}])
    with patch("httpx.Client") as mock_client_class:
        mock_client = mock_client_class.return_value.__enter__.return_value
        mock_client.get.return_value = mock_response

        r = client.get("/api/proxy/modules")
        assert r.status_code == 200
        assert r.json() == [{"id": 1, "name": "Module 1"}]
        mock_client.get.assert_called_once()

def test_add_course_duplicate_course_id(client):
    client.post("/api/add-course", json = add_course_payload())
    r = client.post("/api/add-course", json = add_course_payload())
    assert r.status_code == 409
    assert r.json() == {"detail": "Course could not be created"}

####################################################################################
# Tests for RabbitMQ publish_event through endpoints
####################################################################################

def test_publish_event_on_add_course_with_rabbit(client):
    """Test that publish_event is called when adding a course with RABBIT_URL set"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            r = client.post("/api/add-course", json=add_course_payload(course_id="RABBIT1"))
            assert r.status_code == 201
            # Verify connection was attempted
            mock_connect.assert_called()

def test_publish_event_on_update_course_with_rabbit(client):
    """Test that publish_event is called when updating a course"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            # First add a course
            client.post("/api/add-course", json=add_course_payload(course_id="RABBIT2"))
            # Then update it
            r = client.put("/api/update-course-by-id/RABBIT2", json={"course_name": "Updated", "description": "Updated"})
            assert r.status_code == 200
            # Verify connection was attempted at least once for the update
            assert mock_connect.call_count >= 1

def test_publish_event_on_delete_course_with_rabbit(client):
    """Test that publish_event is called when deleting a course"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            # First add a course
            client.post("/api/add-course", json=add_course_payload(course_id="RABBIT3"))
            # Then delete it
            r = client.delete("/api/delete-course-by-id/RABBIT3")
            assert r.status_code == 200
            assert mock_connect.call_count >= 1

def test_publish_event_on_patch_course_with_rabbit(client):
    """Test that publish_event is called when patching a course"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            # First add a course
            client.post("/api/add-course", json=add_course_payload(course_id="RABBIT4"))
            # Then patch it
            r = client.patch("/api/patch-course-by-id/RABBIT4", json={"course_name": "Patched"})
            assert r.status_code == 200
            assert mock_connect.call_count >= 1

def test_publish_event_on_enroll_with_rabbit(client):
    """Test that publish_event is called when enrolling a user"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            # First add a course
            client.post("/api/add-course", json=add_course_payload(course_id="RABBIT5"))
            # Then enroll a user
            r = client.post("/api/courses/RABBIT5/enroll/g00425075")
            assert r.status_code == 200
            assert mock_connect.call_count >= 1

def test_publish_event_on_unenroll_with_rabbit(client):
    """Test that publish_event is called when unenrolling a user"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection) as mock_connect:
            # First add a course and enroll
            client.post("/api/add-course", json=add_course_payload(course_id="RABBIT6"))
            client.post("/api/courses/RABBIT6/enroll/g00425075")
            # Then unenroll
            r = client.post("/api/courses/RABBIT6/unenroll/g00425075")
            assert r.status_code == 200
            assert mock_connect.call_count >= 1

def test_publish_event_error_handling(client):
    """Test that errors in publish_event don't break the endpoints"""
    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", side_effect=Exception("Connection failed")):
            # Should still work even if RabbitMQ fails
            r = client.post("/api/add-course", json=add_course_payload(course_id="ERROR1"))
            assert r.status_code == 201

def test_multiple_operations_with_rabbit(client):
    """Test multiple operations to ensure publish_event coverage with actual execution"""
    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = None

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection):
            # Add multiple courses
            client.post("/api/add-course", json=add_course_payload(course_id="MULTI1"))
            client.post("/api/add-course", json=add_course_payload(course_id="MULTI2"))

            # Update a course
            client.put("/api/update-course-by-id/MULTI1", json={"course_name": "Updated Multi", "description": "Updated"})

            # Patch a course
            client.patch("/api/patch-course-by-id/MULTI2", json={"course_name": "Patched Multi"})

            # Enroll and unenroll
            client.post("/api/courses/MULTI1/enroll/testuser")
            client.post("/api/courses/MULTI1/unenroll/testuser")

            # Delete
            client.delete("/api/delete-course-by-id/MULTI1")

            # Verify all operations succeeded
            assert mock_exchange.publish.call_count >= 7

def test_add_multiple_courses_with_different_data(client):
    """Test adding multiple courses with various data to increase coverage"""
    # Add courses with different configurations
    r1 = client.post("/api/add-course", json=add_course_payload(course_id="TEST01", course_name="Test Course 1", description="First test"))
    assert r1.status_code == 201

    r2 = client.post("/api/add-course", json=add_course_payload(course_id="TEST02", course_name="Test Course 2", description="Second test"))
    assert r2.status_code == 201

    r3 = client.post("/api/add-course", json=add_course_payload(course_id="TEST03", course_name="Test Course 3", description="A" * 1999))
    assert r3.status_code == 201

    # Verify all added
    all_courses = client.get("/api/get-all-courses").json()
    course_ids = [c["course_id"] for c in all_courses]
    assert "TEST01" in course_ids
    assert "TEST02" in course_ids
    assert "TEST03" in course_ids

####################################################################################
# Direct unit tests for publish_event and process_user_deleted
####################################################################################

def test_publish_event_with_successful_connection():
    """Test publish_event with successful RabbitMQ connection"""
    from app.main import publish_event
    import asyncio

    mock_connection = AsyncMock()
    mock_channel = AsyncMock()
    mock_exchange = AsyncMock()

    mock_channel.declare_exchange.return_value = mock_exchange
    mock_connection.channel.return_value = mock_channel
    mock_connection.__aenter__.return_value = mock_connection
    mock_connection.__aexit__.return_value = AsyncMock()

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", return_value=mock_connection):
            # Run the async function
            asyncio.run(publish_event("test.event", {"test": "data"}))

            # Verify the event was published
            mock_connection.channel.assert_called_once()
            mock_channel.declare_exchange.assert_called_once()
            mock_exchange.publish.assert_called_once()

def test_publish_event_with_connection_failure():
    """Test publish_event handles connection failures gracefully"""
    from app.main import publish_event
    import asyncio

    with patch("app.main.RABBIT_URL", "amqp://localhost"):
        with patch("aio_pika.connect_robust", side_effect=Exception("Connection failed")):
            # Should not raise an exception
            asyncio.run(publish_event("test.event", {"test": "data"}))

def test_process_user_deleted_with_no_user_id():
    """Test process_user_deleted returns early when no user_id"""
    from app.main import process_user_deleted
    import asyncio

    # Should return early without errors
    asyncio.run(process_user_deleted({}))
    asyncio.run(process_user_deleted({"other_field": "value"}))

def test_process_user_deleted_with_database_error():
    """Test process_user_deleted handles database errors gracefully"""
    from app.main import process_user_deleted
    import asyncio
    from unittest.mock import MagicMock

    # Mock SessionLocal to raise an exception during query
    with patch("app.main.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_db.close = MagicMock()
        mock_session_local.return_value = mock_db

        # Should handle error gracefully without raising
        asyncio.run(process_user_deleted({"user_id": "testuser"}))

        # Verify rollback and close were called
        mock_db.rollback.assert_called_once()
        mock_db.close.assert_called_once()

