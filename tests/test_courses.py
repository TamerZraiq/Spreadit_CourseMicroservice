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
    r = client.post("/api/add-course", json = {"course_id": "12", "course_name": "Robotics", "description": "Drones"})
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