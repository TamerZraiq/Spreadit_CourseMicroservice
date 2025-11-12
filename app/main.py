# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, SessionLocal
from app.models import Base, CourseDB
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .schemas import Course, AddCourse, UpdateCourse
import httpx

#Replacing @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)   
    yield

app = FastAPI(lifespan=lifespan)

courses: list[Course] = []

# CORS (add this block)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # dev-friendly; tighten in prod
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

@app.get("/health")
def health():
    return {"status": "ok"}



#using db to get users
@app.get("/api/get-all-courses", response_model=list[Course])
def get_courses(db: Session = Depends(get_db)):
    stmt = select(CourseDB).order_by(CourseDB.id)
    return list(db.execute(stmt).scalars())



#get user by user id from db
@app.get("/api/course-by-id/{course_id}", response_model=Course)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()
    if not course: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found") #if not found return 404
    return course


#Add course
@app.post("/api/add-course", response_model=AddCourse, status_code=status.HTTP_201_CREATED)
def add_course(payload: AddCourse, db: Session = Depends(get_db)):
    course = CourseDB(**payload.model_dump())
    db.add(course)
    commit_or_rollback(db, "Course could not be created")
    return course

#get course by id
@app.get("/api/get-course-by-id/{course_id}", response_model=Course)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()
    if not course: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found") #if not found return 404
    return course

#update course by id
@app.put("/api/update-course-by-id/{course_id}", status_code=status.HTTP_200_OK)
def update_course(course_id: str, updated_course: UpdateCourse, db: Session = Depends(get_db)):
    result = db.query(CourseDB).filter(CourseDB.course_id == course_id).update(updated_course.model_dump())
    db.commit()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="id not found")

    return {"message": "Course updated successful"}


#delete course by id
@app.delete("/api/delete-course-by-id/{course_id}", status_code=status.HTTP_200_OK)
def delete_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()
    db.delete(course)
    db.commit()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course_id not found")

    return {"message": "Deleted Course"}

#enroll function
@app.post("/courses/{course_id}/enroll/{user_id}")
def enroll_user(course_id: str, user_id: str, db: Session = Depends(get_db)):
    # Get course
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Initialize list if null (sqlite json quirk)
    if course.enrolled_users is None:
        course.enrolled_users = []

    # Prevent duplicates
    if user_id in course.enrolled_users:
        raise HTTPException(status_code=409, detail="User already enrolled in course")

    # Add user id to course
    course.enrolled_users.append(user_id)
    db.commit()
    db.refresh(course)

    return {"message": f"User {user_id} enrolled in course {course_id}"}
