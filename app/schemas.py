# app/schemas.py
from pydantic import BaseModel, constr, conint

class Course(BaseModel):
    id: int
    course_id: constr(pattern=r'^\d{4}$')
    course_name: constr(min_length=2, max_length=50)
    description: constr(min_length=2, max_length=100)