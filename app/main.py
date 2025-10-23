# app/main.py
from fastapi import FastAPI, HTTPException, status
from .schemas import Course

app = FastAPI()
courses: list[Course] = []


@app.get("/api/course")
def get_course():
    return courses

@app.get("/api/course/{course_id}")
def get_course_by_id(course_id: str):
    for c in courses:
        if c.course_id == course_id:
            return c
    raise HTTPException(status_code=404, detail="course not found")


@app.post("/api/course", status_code=status.HTTP_201_CREATED)
def add_course(course: Course):
    if any(c.course_id == course.course_id for c in courses):
        raise HTTPException(status_code=409, detail="course_id already exists")
    courses.append(course)
    return course


@app.put("/api/course/{course_id}", status_code=status.HTTP_200_OK)
def update_course(course_id: str, updated_course: Course):
    for i, c in enumerate(courses):
        if c.course_id == course_id:
            courses[i] = updated_course
            return updated_course
    raise HTTPException(status_code=404, detail="course not found")


@app.delete("/api/course/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: str):
    for c in courses:
        if c.course_id == course_id:
            courses.remove(c)
            return
    raise HTTPException(status_code=404, detail="course not found")