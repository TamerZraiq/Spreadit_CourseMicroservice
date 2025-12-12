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
import os
import aio_pika
import json
import asyncio

MODULE_SERVICE_URL = os.getenv("MODULE_SERVICE_URL", "http://localhost:8000")
RABBIT_URL = os.getenv("RABBIT_URL")

async def publish_event(routing_key: str, data: dict):
    if not RABBIT_URL:
        print("RABBIT_URL not set, skipping message publish")
        return
        
    try:
        connection = await aio_pika.connect_robust(RABBIT_URL)
        async with connection:
            channel = await connection.channel()
            exchange = await channel.declare_exchange("events_topic", aio_pika.ExchangeType.TOPIC)
            
            message = aio_pika.Message(
                body=json.dumps(data).encode(),
                content_type="application/json"
            )
            await exchange.publish(message, routing_key=routing_key)
            print(f"Published event: {routing_key}")
    except Exception as e:
        print(f"Failed to publish event {routing_key}: {e}")

async def process_user_deleted(data: dict):
    user_id = data.get("user_id")
    if not user_id:
        return
    
    print(f"Processing user deletion for: {user_id}")
    db = SessionLocal()
    try:
        # Find courses where user is enrolled
        # Note: .contains uses JSON semantics. 
        courses = db.query(CourseDB).filter(CourseDB.enrolled_users.contains([user_id])).all()
        for course in courses:
            if user_id in course.enrolled_users:
                course.enrolled_users.remove(user_id)
                # Force SQLAlchemy to detect the change in MutableList
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(course, "enrolled_users")
        
        db.commit()
        print(f"Removed user {user_id} from {len(courses)} courses.")
    except Exception as e:
        print(f"Error processing user deletion: {e}")
        db.rollback()
    finally:
        db.close()

async def consume_events():
    if not RABBIT_URL:
        print("RABBIT_URL not set, skipping consumer")
        return

    while True:
        try:
            connection = await aio_pika.connect_robust(RABBIT_URL)
            async with connection:
                channel = await connection.channel()
                
                # Declare exchange and queue
                await channel.declare_exchange("events_topic", aio_pika.ExchangeType.TOPIC)
                queue = await channel.declare_queue("course_service_queue", durable=True)
                
                # Bind to events we care about
                await queue.bind("events_topic", routing_key="user.deleted")
                
                print("Course Service Consumer Started")
                
                async with queue.iterator() as iterator:
                    async for message in iterator:
                        async with message.process():
                            data = json.loads(message.body)
                            if message.routing_key == "user.deleted":
                                await process_user_deleted(data)
                                
        except asyncio.CancelledError:
            print("Consumer cancelled")
            break
        except Exception as e:
            print(f"Consumer connection lost: {e}, retrying in 5s...")
            await asyncio.sleep(5)

#Replacing @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)   
    # Start the consumer in the background
    task = asyncio.create_task(consume_events())
    yield
    # We could cancel the task here, but for now we let it die with the app

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
@app.get("/api/course-by-user-id/{user_id}", response_model=Course)
def get_course(user_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.enrolled_users.contains([user_id])).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found for the specific user") #if not found return 404
    return course


#Add course
@app.post("/api/add-course", response_model=Course, status_code=status.HTTP_201_CREATED)
async def add_course(payload: AddCourse, db: Session = Depends(get_db)):
    course = CourseDB(**payload.model_dump())
    db.add(course)
    commit_or_rollback(db, "Course could not be created")
    
    # Publish event
    await publish_event("course.created", {
        "course_id": course.course_id,
        "name": course.name
    })
    
    return course

#get course by course_id (string like "CS101")
@app.get("/api/get-course-by-id/{course_id}", response_model=Course)
def get_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()
    if not course: 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found") #if not found return 404
    return course

#get course by database id (integer like 1, 2, 3)
@app.get("/api/get-course-by-db-id/{db_id}", response_model=Course)
def get_course_by_db_id(db_id: int, db: Session = Depends(get_db)):
    course = db.get(CourseDB, db_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return course

#update course by id
@app.put("/api/update-course-by-id/{course_id}", status_code=status.HTTP_200_OK)
async def update_course(course_id: str, updated_course: UpdateCourse, db: Session = Depends(get_db)):
    result = db.query(CourseDB).filter(CourseDB.course_id == course_id).update(updated_course.model_dump())
    db.commit()

    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="id not found")

    # Publish event
    await publish_event("course.updated", {
        "course_id": course_id,
        "updated_validation": updated_course.model_dump()
    })

    return {"message": "Course updated successful"}

#Partial update course by ID
@app.patch("/api/patch-course-by-id/{course_id}", status_code=status.HTTP_200_OK)
async def patch_course(course_id: str, patched_course: UpdateCourse, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()

    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course ID not found")
    
    updated_field = patched_course.model_dump(exclude_unset=True)

    for field, value in updated_field.items():
        setattr(course, field, value)

    commit_or_rollback(db, "Course patch failed")
    db.refresh(course)
    
    # Publish event
    await publish_event("course.patched", {
        "course_id": course_id,
        "updated_field": updated_field
    })
    
    return {"message": "Course patched successful"}

#delete course by id
@app.delete("/api/delete-course-by-id/{course_id}", status_code=status.HTTP_200_OK)
async def delete_course(course_id: str, db: Session = Depends(get_db)):
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="course_id not found for delete")

    db.delete(course)
    db.commit()

    # Publish event
    await publish_event("course.deleted", {
        "course_id": course_id
    })

    return {"message": "Deleted Course"}

#enroll function
@app.post("/api/courses/{course_id}/enroll/{user_id}", status_code = status.HTTP_200_OK)
async def enroll_user(course_id: str, user_id: str, db: Session = Depends(get_db)):
    # Get course
    course = db.query(CourseDB).filter(CourseDB.course_id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # # Initialize list if null (sqlite json quirk)
    # if course.enrolled_users is None:
    #     course.enrolled_users = []

    # Prevent duplicates
    if user_id in course.enrolled_users:
        raise HTTPException(status_code=409, detail="User already enrolled in course")

    # Add user id to course
    course.enrolled_users.append(user_id)
    db.commit()
    db.refresh(course)

    # Publish event
    await publish_event("course.enrolled", {
        "course_id": course_id,
        "user_id": user_id
    })

    return {"message": f"User {user_id} enrolled in course {course_id}"}

@app.get("/api/proxy/modules")
def proxy_modules():
    with httpx.Client() as client:
        response = client.get(f"{MODULE_SERVICE_URL}/api/module")
    return response.json()