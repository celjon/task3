import os
from bson import ObjectId
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from dotenv import load_dotenv

load_dotenv(".env")
MONGODB_URL = os.getenv("MONGODB_URL", default="mongodb://localhost:27017/test_database")

app = FastAPI()
async def get_student_collection(request: Request):
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client['test_database']
    return mongo_client['students']


async def get_group_collection(request: Request):
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client['test_database']
    return mongo_client['groups']


@app.post("/students")
async def create_student(request: Request, student_data: dict) -> dict:
    student_collection = await get_student_collection(request)
    result = await student_collection.insert_one(student_data)
    student_id = str(result.inserted_id)
    return {"student_id": student_id}


@app.post("/groups")
async def create_group(request: Request, group_data: dict) -> dict:
    group_collection = await get_group_collection(request)
    result = await group_collection.insert_one(group_data)
    group_id = str(result.inserted_id)
    return {"id": group_id}


@app.get("/students/{student_id}")
async def get_student(request: Request, student_id: str) -> dict:
    student_collection = await get_student_collection(request)
    student = await student_collection.find_one({"_id": ObjectId(student_id)})

    if student:
        student["_id"] = str(student["_id"])
        return student
    else:
        raise HTTPException(status_code=404, detail="Student not found")


@app.get("/groups/{group_id}")
async def get_group(request: Request, group_id: str) -> dict:
    group_collection = await get_group_collection(request)
    group = await group_collection.find_one({"_id": ObjectId(group_id)})

    if group:
        group["_id"] = str(group["_id"])
        return group
    else:
        raise HTTPException(status_code=404, detail="Group not found")


@app.delete("/students/{student_id}")
async def delete_student(request: Request, student_id: str) -> dict:
    student_collection = await get_student_collection(request)
    result = await student_collection.delete_one({"_id": ObjectId(student_id)})

    if result.deleted_count > 0:
        return {"message": "Student deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")


@app.delete("/groups/{group_id}")
async def delete_group(request: Request, group_id: str) -> dict:
    group_collection = await get_group_collection(request)
    result = await group_collection.delete_one({"_id": ObjectId(group_id)})

    if result.deleted_count > 0:
        return {"message": "Group deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Group not found")


@app.get("/students")
async def get_students(request: Request) -> list:
    student_collection = await get_student_collection(request)
    cursor = student_collection.find({})
    students = []

    async for document in cursor:
        document["_id"] = str(document["_id"])
        students.append(document)

    return students


@app.get("/groups")
async def get_groups(request: Request) -> list:
    group_collection = await get_group_collection(request)
    cursor = group_collection.find({})
    groups = []

    async for document in cursor:
        document["_id"] = str(document["_id"])
        groups.append(document)

    return groups


@app.put("/students/{student_id}/group/{group_id}")
async def add_student_to_group(request: Request, student_id: str, group_id: str) -> dict:
    student_collection = await get_student_collection(request)
    group_collection = await get_group_collection(request)

    student = await student_collection.find_one({"_id": ObjectId(student_id)})
    group = await group_collection.find_one({"_id": ObjectId(group_id)})

    if student and group:
        await student_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"group_id": ObjectId(group_id)}})
        return {"message": "Student added to group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or group not found")


@app.delete("/students/{student_id}/group")
async def remove_student_from_group(request: Request, student_id: str) -> dict:
    student_collection = await get_student_collection(request)
    student = await student_collection.find_one({"_id": ObjectId(student_id)})

    if student and student.get("group_id"):
        await student_collection.update_one({"_id": ObjectId(student_id)}, {"$unset": {"group_id": ""}})
        return {"message": "Student removed from group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or group not found")


@app.get("/groups/{group_id}/students")
async def get_students_in_group(request: Request, group_id: str) -> list:
    student_collection = await get_student_collection(request)
    students = await student_collection.find({"group_id": group_id}).to_list(length=100)

    for student in students:
        student["_id"] = str(student["_id"])

    return students



@app.put("/students/{student_id}/transfer/{new_group_id}")
async def transfer_student(request: Request, student_id: str, new_group_id: str) -> dict:
    student_collection = await get_student_collection(request)
    group_collection = await get_group_collection(request)

    student = await student_collection.find_one({"_id": ObjectId(student_id)})
    new_group = await group_collection.find_one({"_id": ObjectId(new_group_id)})

    if student and new_group:
        await student_collection.update_one({"_id": ObjectId(student_id)}, {"$set": {"group_id": ObjectId(new_group_id)}})
        return {"message": "Student transferred to new group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or new group not found")

client = AsyncIOMotorClient(MONGODB_URL)

app.state.mongo_client = client

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
