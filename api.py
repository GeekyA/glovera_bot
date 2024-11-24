import json
import logging
import os
import shutil
from tempfile import NamedTemporaryFile
import base64
from bson.errors import InvalidId
from bson.objectid import ObjectId
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
    Path,
    Request,
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ValidationError
from datetime import datetime
from datetime import datetime

from utils.database import get_collection_by_name, get_db_connection
from llm.glovera_chat import OpenAIConversation
from llm.openai_tts import generate_speech
from llm.groq_stt import stt
from utils.models import User, TTSRequest, STTRequest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = FastAPI()

# MongoDB collection
db = get_db_connection()
conversations_collection = get_collection_by_name(db, 'Conversation')
users_collection = get_collection_by_name(db,'Profile')


@router.post("/start_conversation/")
async def start_conversation(
    user_id: str = Form(...),
    get_audio_response: bool = Form(False),
    user_id: str = Form(...),
    get_audio_response: bool = Form(False),
):
    response = {"success": False, "message": "", "data": None}
    print({"userId":ObjectId(user_id)})
    user_info = users_collection.find_one({"userId":ObjectId(user_id)})
    
    if not user_info:
        raise HTTPException(status_code=500, detail="Internal server error")


    user_info = dict([(i,user_info[i]) for i in user_info if i != '_id' and i != 'userId'])
    # print(user_info)
    try:
        # Initialize conversation
        prompt_system = """You are an AI consultant to help users who want to study abroad.
        Answer all their questions regarding courses, universities, eligibility, etc.

        IMPORTANT: When users ask about courses or universities, ALWAYS use the query_mongodb function to search the database first.

        Here's how to use it:
        1. For questions about courses/universities, ALWAYS create a MongoDB query using the query_mongodb function
        2. The query should be in this format:
            {
                "$and": [
                    { "university_location": { "$regex": "country|alternative names", "$options": "i" } },
                    { "course_name": { "$regex": "subject|related terms", "$options": "i" } }
                ]
            }
        3. Wait for the query results and then provide a natural response based on the data

        Examples:
        - If user asks about "CS in UK": Use query with "computer|computing" for course and "uk|united kingdom|england" for location
        - If user asks about "MBA in USA": Use query with "business|mba|administration" for course and "usa|united states" for location
        For more info here is the db schema as well
            "course_name": Name of the course,
            "degree_type": Type of degree (e.g., M.Sc.),
            "tuition_fee": Course fee,
            "duration": Course length (e.g., '1 year'),
            "university_name": University name,
            "university_location": University location,
            "global_rank": University ranking,
            "english_requirments": Minimum language scores, contains three more fields ( {"ielts": ielts_score, "toefl": toefl_score, "pte"pte_score})
            "min_gpa": Required GPA,
            "work_experience": Relevant work experience,
            "start_date": Course start date,
            "apply_date": Application deadline

        NEVER skip the database query - it's essential for providing accurate information.
        The query will be automatically called in the background and you never show the query to the user, just use the data 
        returned by the query to augment your response
        Tailor your responses keeping in mind that they'll be parsed by a Text-to-speech model
        In a natural human-like conversation. Your responses will be sent to a TTS system, so go light on bullet points."""

        prompt_system += f"Also, here is some additional information about the user to help you respond better {user_info}"

        initial_message = (
            "Hi, I am an AI consultant who'll help you find the best universities abroad. "
            "Ask me anything about where you want to study, what you want to study, your budget, "
            "or any other questions you might have.")

        conversation = OpenAIConversation(
            model="gpt-4o", system_prompt=prompt_system
        )

        conversation = OpenAIConversation(model="gpt-4o", system_prompt=prompt_system)
        conversation.start_conversation(initial_message=initial_message)

        # Create conversation document matching Prisma schema
        # Create conversation document matching Prisma schema
        conv_to_post = {
            "userId": user_id,
            "title": "Study Abroad Consultation",
            "messages": [{
                "role": "system",
                "content": prompt_system,
                "timestamp": str(datetime.utcnow())
            }, {
                "role": "assistant",
                "content": initial_message,
                "timestamp": str(datetime.utcnow())
            }],
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow(),
            "status": "active"
        }

        # Store in database
        result = conversations_collection.insert_one(conv_to_post)
        conversation_id = str(result.inserted_id)
        result = conversations_collection.insert_one(conv_to_post)
        conversation_id = str(result.inserted_id)

        # Generate audio if required
        if get_audio_response:
            try:
                with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    audio_path = temp_file.name
                    generate_speech(initial_message, output_file=audio_path)
        if get_audio_response:
            try:
                with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                    audio_path = temp_file.name
                    generate_speech(initial_message, output_file=audio_path)

                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = base64.b64encode(
                            audio_file.read()).decode("utf-8")

                    os.unlink(audio_path)
                    os.unlink(audio_path)

                    response["success"] = True
                    response["message"] = "Conversation started successfully"
                    response["data"] = {
                        "conversation_id": conversation_id,
                        "initial_message": initial_message,
                        "audio_response": audio_bytes,
                    }
                    return response
                    response["success"] = True
                    response["message"] = "Conversation started successfully"
                    response["data"] = {
                        "conversation_id": conversation_id,
                        "initial_message": initial_message,
                        "audio_response": audio_bytes,
                    }
                    return response

            except Exception as e:
                logger.error(f"Audio generation error: {str(e)}")
                response["success"] = True
                response["message"] = "Conversation started but audio generation failed"
                response["data"] = {
                    "conversation_id": conversation_id,
                    "initial_message": initial_message,
                    "error": "Failed to generate audio response",
                }
                return response
            except Exception as e:
                logger.error(f"Audio generation error: {str(e)}")
                response["success"] = True
                response["message"] = "Conversation started but audio generation failed"
                response["data"] = {
                    "conversation_id": conversation_id,
                    "initial_message": initial_message,
                    "error": "Failed to generate audio response",
                }
                return response

        response["success"] = True
        response["message"] = "Conversation started successfully"
        response["data"] = {
            "conversation_id": conversation_id,
            "initial_message": initial_message
        }
        return response

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/continue_conversation/")
async def continue_conversation(
    conversation_id: str = Form(...),
    message: str = Form(...),
    message: str = Form(...),
    get_audio_response: bool = Form(False),
    audio_base64: str = Form(None),
    audio_base64: str = Form(None),
):
    temp_files = []
    try:
        # Validate conversation_id format
        try:
            obj_id = ObjectId(conversation_id)
        except InvalidId:
            raise HTTPException(
                status_code=400, detail="Invalid conversation ID format")

        # Find the conversation
        conversation = conversations_collection.find_one({
            "_id": obj_id
        })

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found")

        # Process audio input if provided
        user_message = message
        if audio_base64:
            try:
                with NamedTemporaryFile(suffix=".wav", delete=False) as temp_input:
                    temp_files.append(temp_input.name)
                    content = base64.b64decode(audio_base64)
                    temp_input.write(content)
                    temp_input.flush()
                    user_message = stt(temp_input.name, lang="en", system="")
            except Exception as e:
                logger.error(f"Audio processing error: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Failed to process audio input")

        # Add user message
        new_message = {
            "role": "user",
            "content": user_message,
            "timestamp": str(datetime.utcnow())
        }

        # Get AI response
        ai = OpenAIConversation(model="gpt-4o")
        ai.set_conversation(conversation["messages"])
        ai_response = ai.add_user_message(user_message)

        # Add AI response message
        ai_message = {
            "role": "assistant",
            "content": ai_response,
            "timestamp": str(datetime.utcnow())
        }

        # Update conversation
        conversations_collection.update_one(
            {"_id": obj_id},
            {
                "$push": {"messages": {"$each": [new_message, ai_message]}},
                "$set": {"updatedAt": datetime.utcnow()}
            }
        )

        # Generate audio response if requested
        if get_audio_response:
            try:
                with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output:
                    temp_files.append(temp_output.name)
                    generate_speech(ai_response, output_file=temp_output.name)

                    with open(temp_output.name, "rb") as audio_file:
                        audio_base64 = base64.b64encode(
                            audio_file.read()).decode("utf-8")

                    return {
                        "success": True,
                        "message": "Response generated successfully",
                        "data": {
                            "audio_base64": audio_base64,
                            "user_message": user_message,
                            "ai_response": ai_response
                        }
                    }

            except Exception as e:
                logger.error(f"Speech generation error: {str(e)}")
                return {
                    "success": True,
                    "message": "Response generated but audio conversion failed",
                    "data": {
                        "ai_response": ai_response,
                        "user_message": user_message
                    }
                }

        return {
            "success": True,
            "message": "Response generated successfully",
            "data": {
                "ai_response": ai_response,
                "user_message": user_message
            }
        }

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")


@router.post("/standalone_tts")
async def tts(request: TTSRequest):
    response = {"success": False, "message": "", "data": None}
    logger.info(json.dumps(request.dict(), indent=2))

    try:
        if not request.text:
            raise HTTPException(status_code=400, detail="Text is required")
            raise HTTPException(status_code=400, detail="Text is required")

        with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output:
            output_file = temp_output.name
            generate_speech(request.text, output_file=output_file)

            with open(output_file, "rb") as audio_file:
                audio_base64 = base64.b64encode(
                    audio_file.read()).decode("utf-8")

            response["success"] = True
            response["message"] = "Text-to-speech conversion successful"
            response["data"] = {"audio_base64": audio_base64}

            os.unlink(output_file)
            return response
            return response

    except Exception as e:
        logger.error(f"TTS generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
        raise HTTPException(status_code=500, detail="Internal server error")
