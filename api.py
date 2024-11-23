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

from utils.database import get_conversations_collection
from llm.glovera_chat import OpenAIConversation
from llm.openai_tts import generate_speech
from llm.groq_stt import stt
from utils.models import User, TTSRequest, STTRequest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = FastAPI()

# MongoDB collection
conversations_collection = get_conversations_collection()

@router.post("/start_conversation/")
async def start_conversation(
    user: User = Form(),
    get_audio_response: bool = False
):
    response = {"success": False, "message": "", "data": None}

    try:
        # Initialize conversation
        prompt_system = (
        "You are an AI consultant to help users who want to study abroad.\n"
        "Answer all their questions regarding courses, universities, eligibility, etc.\n"
        "Tailor your responses keeping in mind that they'll be parsed by a Text-to-speech model\n"
        "In a natural human-like conversation")

        initial_message = (
        "Hi, I am an AI consultant who'll help you find the best universities abroad. "
        "Ask me anything about where you want to study, what you want to study, your budget, "
        "or any other questions you might have.")

        conversation = OpenAIConversation(
            model="gpt-4o", system_prompt=prompt_system
        )
        conversation.start_conversation(initial_message=initial_message)

        # Prepare conversation data
        conv_to_post = {
            "user": user.dict(),
            "messages": conversation.messages,
        }

        # Store in database
        try:
            result = conversations_collection.insert_one(conv_to_post)
            conversation_id = str(result.inserted_id)
        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            response["message"] = "Failed to store conversation"
            return JSONResponse(status_code=500, content=response)

        # Generate audio if required
        try:
            if not get_audio_response:
                response["success"] = True
                response["message"] = "Conversation started successfully"
                response["data"] = {
                    "conversation_id": conversation_id,
                    "initial_message": initial_message,
                }
                return response
            with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                audio_path = temp_file.name
                generate_speech(initial_message, output_file=audio_path)

                with open(audio_path, "rb") as audio_file:
                    audio_bytes = base64.b64encode(audio_file.read()).decode("utf-8")

                os.unlink(audio_path)

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

    except ValidationError as e:
        response["message"] = str(e)
        return JSONResponse(status_code=422, content=response)

    except Exception as e:
        logger.error(f"Error in starting conversation: {str(e)}")
        response["message"] = "Internal server error"
        return JSONResponse(status_code=500, content=response)


@router.post("/continue_conversation/")
async def continue_conversation(
    conversation_id: str = Form(...),
    user_response: str = Form(...),
    get_audio_response: bool = Form(False),
    audio_base64: str = Form(None)
):
    response = {"success": False, "message": "", "data": None}

    temp_files = []

    try:
        # Validate conversation_id format
        try:
            obj_id = ObjectId(conversation_id)
        except InvalidId:
            response["message"] = "Invalid conversation ID format"
            return JSONResponse(status_code=400, content=response)

        # Find the conversation
        conversation_doc = conversations_collection.find_one({"_id": obj_id})
        if not conversation_doc:
            response["message"] = "Conversation not found"
            return JSONResponse(status_code=404, content=response)

        # Extract messages and create conversation
        messages = conversation_doc.get("messages", [])
        conversation = OpenAIConversation(model="gpt-4o-mini")
        conversation.set_conversation(conversation=messages)

        # Process user input (either audio_base64 or text)
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
                response["message"] = "Failed to process audio input"
                return JSONResponse(status_code=500, content=response)
        else:
            if not user_response:
                response["message"] = (
                    "User response is required when audio is not provided"
                )
                return JSONResponse(status_code=400, content=response)
            user_message = user_response

        # Get AI response
        ai_response = conversation.add_user_message(user_message)

        # Update conversation in database
        try:
            conversations_collection.update_one(
                {"_id": obj_id}, {"$set": {"messages": conversation.get_conversation()}}
            )
        except Exception as e:
            logger.error(f"Database update error: {str(e)}")
            response["message"] = "Failed to update conversation"
            return JSONResponse(status_code=500, content=response)

        # Generate audio response if requested
        if get_audio_response:
            try:
                with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output:
                    temp_files.append(temp_output.name)
                    generate_speech(ai_response, output_file=temp_output.name)
                    response_path = f"/tmp/response_{conversation_id}.mp3"
                    shutil.copy2(temp_output.name, response_path)

                    async def cleanup_response_file():
                        try:
                            if os.path.exists(response_path):
                                os.unlink(response_path)
                        except Exception as e:
                            logger.error(f"Failed to cleanup response file: {str(e)}")

                    with open(response_path, "rb") as audio_file:
                        audio_base64 = base64.b64encode(audio_file.read()).decode(
                            "utf-8"
                        )

                    response["success"] = True
                    response["message"] = "Response generated successfully"
                    response["data"] = {
                        "audio_base64": audio_base64,
                        "user_message": user_message,
                        "ai_response": ai_response,
                    }

                    return JSONResponse(
                        status_code=200,
                        content=response,
                        background=cleanup_response_file,
                    )
            except Exception as e:
                logger.error(f"Speech generation error: {str(e)}")
                response["success"] = True
                response["message"] = "Response generated but audio conversion failed"
                response["data"] = {"ai_response": ai_response}
                return JSONResponse(status_code=200, content=response)

        # Return text response
        response["success"] = True
        response["message"] = "Response generated successfully"
        response["data"] = {"ai_response": ai_response}
        return response

    except Exception as e:
        logger.error(f"Error in continue_conversation: {str(e)}")
        response["message"] = "Internal server error"
        return JSONResponse(status_code=500, content=response)

    finally:
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                logger.error(f"Failed to cleanup temporary file {temp_file}: {str(e)}")


@router.post("/standalone_tts")
async def tts(
    request: TTSRequest
):
    response = {"success": False, "message": "", "data": None}
    logger.info(json.dumps(request.dict(), indent=2))

    try:
        if not request.text:
            response["message"] = "Text is required"
            return JSONResponse(status_code=400, content=response)

        with NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output:
            output_file = temp_output.name
            generate_speech(request.text, output_file=output_file)

            # Read the audio file and encode it to base64
            with open(output_file, "rb") as audio_file:
                audio_base64 = base64.b64encode(audio_file.read()).decode("utf-8")

            # Prepare the response
            response["success"] = True
            response["message"] = "Text-to-speech conversion successful"
            response["data"] = {"audio_base64": audio_base64}

            # Clean up temporary file after response
            os.unlink(output_file)
            return JSONResponse(status_code=200, content=response)

    except Exception as e:
        logger.error(f"TTS generation error: {str(e)}")
        response["message"] = "Internal server error"
        return JSONResponse(status_code=500, content=response)
