import motor.motor_asyncio
import uvicorn
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, FastAPI, HTTPException
from envparse import Env
from fastapi.routing import APIRoute
from starlette.requests import Request

env = Env()
MONGODB_URL = env.str("MONGODB_URL", default="mongodb://localhost:27017/test_database")


async def ping() -> dict:
    return {"Success": True}


async def create_student(request: Request, student_data: dict) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    student = await mongo_client.students.insert_one(student_data)
    return {"id": str(student.inserted_id)}


async def create_group(request: Request, group_data: dict) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    group = await mongo_client.groups.insert_one(group_data)
    return {"id": str(group.inserted_id)}


async def get_student(request: Request, student_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    student = await mongo_client.students.find_one({"_id": student_id})
    if student:
        student["_id"] = str(student["_id"])
        return student
    else:
        raise HTTPException(status_code=404, detail="Student not found")


async def get_group(request: Request, group_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    group = await mongo_client.groups.find_one({"_id": group_id})
    if group:
        group["_id"] = str(group["_id"])
        return group
    else:
        raise HTTPException(status_code=404, detail="Group not found")


async def delete_student(request: Request, student_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    result = await mongo_client.students.delete_one({"_id": student_id})
    if result.deleted_count > 0:
        return {"message": "Student deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student not found")


async def delete_group(request: Request, group_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    result = await mongo_client.groups.delete_one({"_id": group_id})
    if result.deleted_count > 0:
        return {"message": "Group deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Group not found")


async def get_students(request: Request) -> list:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    cursor = mongo_client.students.find({})
    students = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        students.append(document)
    return students


async def get_groups(request: Request) -> list:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    cursor = mongo_client.groups.find({})
    groups = []
    async for document in cursor:
        document["_id"] = str(document["_id"])
        groups.append(document)
    return groups


async def add_student_to_group(request: Request, student_id: str, group_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    student = await mongo_client.students.find_one({"_id": student_id})
    group = await mongo_client.groups.find_one({"_id": group_id})
    if student and group:
        await mongo_client.students.update_one({"_id": student_id}, {"$set": {"group_id": group_id}})
        return {"message": "Student added to group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or group not found")


async def remove_student_from_group(request: Request, student_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    student = await mongo_client.students.find_one({"_id": student_id})
    if student and student.get("group_id"):
        await mongo_client.students.update_one({"_id": student_id}, {"$unset": {"group_id": ""}})
        return {"message": "Student removed from group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or group not found")


async def get_students_in_group(request: Request, group_id: str) -> list:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    students = await mongo_client.students.find({"group_id": group_id}).to_list(length=100)
    for student in students:
        student["_id"] = str(student["_id"])
    return students


async def transfer_student(request: Request, student_id: str, new_group_id: str) -> dict:
    mongo_client: AsyncIOMotorClient = request.app.state.mongo_client
    student = await mongo_client.students.find_one({"_id": student_id})
    group = await mongo_client.groups.find_one({"_id": new_group_id})
    if student and group:
        await mongo_client.students.update_one({"_id": student_id}, {"$set": {"group_id": new_group_id}})
        return {"message": "Student transferred to new group successfully"}
    else:
        raise HTTPException(status_code=404, detail="Student or new group not found")


routes = [
    APIRoute(path="/ping", endpoint=ping, methods=["GET"]),
    APIRoute(path="/students", endpoint=create_student, methods=["POST"]),
    APIRoute(path="/groups", endpoint=create_group, methods=["POST"]),
    APIRoute(path="/students/{student_id}", endpoint=get_student, methods=["GET"]),
    APIRoute(path="/groups/{group_id}", endpoint=get_group, methods=["GET"]),
    APIRoute(path="/students/{student_id}", endpoint=delete_student, methods=["DELETE"]),
    APIRoute(path="/groups/{group_id}", endpoint=delete_group, methods=["DELETE"]),
    APIRoute(path="/students", endpoint=get_students, methods=["GET"]),
    APIRoute(path="/groups", endpoint=get_groups, methods=["GET"]),
    APIRoute(path="/students/{student_id}/groups/{group_id}", endpoint=add_student_to_group, methods=["PUT"]),
    APIRoute(path="/students/{student_id}/groups", endpoint=remove_student_from_group, methods=["DELETE"]),
    APIRoute(path="/groups/{group_id}/students", endpoint=get_students_in_group, methods=["GET"]),
    APIRoute(path="/students/{student_id}/transfer/{new_group_id}", endpoint=transfer_student, methods=["PUT"]),
]

client = AsyncIOMotorClient(MONGODB_URL)
app = FastAPI()
app.state.mongo_client = client
app.include_router(APIRouter(routes=routes))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
