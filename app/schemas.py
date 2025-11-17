from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, constr, EmailStr, ConfigDict, StringConstraints, Field

CourseId = Annotated[str, StringConstraints(pattern=r"^\d{4}$")]
CourseName = Annotated[str, StringConstraints(min_length=2, max_length=50)]
DescStr = Annotated[str, StringConstraints(min_length=0, max_length=2000)]

class Course(BaseModel):
    id: int
    course_id: CourseId
    course_name: CourseName
    description: DescStr
    enrolled_users: List[str] = []
    model_config = ConfigDict(from_attributes=True)

class AddCourse(BaseModel):
    course_id: CourseId
    course_name: CourseName
    description: DescStr
    enrolled_users: List[str] = []

class UpdateCourse(BaseModel):
    course_name: Optional[CourseName] = None
    description: Optional[DescStr] = None
