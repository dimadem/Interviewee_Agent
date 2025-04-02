from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import base64
import json
import os

from app.model.ttt import TTT
from app.model.stt import STT
from app.model.tts import TTS

from app.agents.prompts.utils import load_prompts
from pprint import pp

from agents import Runner
from app.agents.interviewee_agent import create_interviewee_agent

# Создаем директорию для временных файлов
# Используем абсолютный путь к директории temp
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

router = APIRouter()

ttt = TTT()
stt = STT()
tts = TTS()

prompts = load_prompts("persona_system_prompt.yaml")

@router.websocket("/ws/interview")
async def websocket_interview(ws: WebSocket, 
                              persona: str = Query("Junior Python Developer"),
                              skill: str = Query("Python programming")):
    await ws.accept()
    
    # Формируем системный промпт с указанными значениями
    system_prompt = prompts["persona_system_prompt"].format(persona=persona, skill=skill)
    
    # Создаем агента один раз при установке соединения
    agent = create_interviewee_agent(system_prompt)
    
    pp(f"WebSocket connected with persona: {persona}, skill: {skill}")
    
    try:
        while True:
            data = await ws.receive_text()
            is_audio = None
            user_input = ""
            messages = []

            try:
                json_data = json.loads(data)
                message_type = json_data['type']

                if message_type == "text":
                    # Если текстовое сообщение, то просто берем его
                    user_input = json_data.get("message", "")
                    is_audio = False
                elif message_type == "audio":
                    audio_bytes = base64.b64decode(json_data["audio"])
                    
                    # Сохраняем аудио во временный файл с использованием абсолютного пути
                    temp_audio_path = os.path.join(TEMP_DIR, "temp_audio.wav")
                    with open(temp_audio_path, "wb") as f:
                        f.write(audio_bytes)
                    user_input = stt.transcribe_from_path(temp_audio_path)
                    is_audio = True
                
                # # Получаем историю сообщений с фронтенда, если она есть
                if 'history' in json_data and json_data['history']:
                    # Преобразуем историю в формат, понятный агенту
                    messages = [
                        ttt.create_chat_message(msg["role"], msg["content"])
                        for msg in json_data['history']
                    ]
            except Exception as e:
                pp(f"Error processing data: {str(e)}")
                await ws.send_json({"type": "error", "text": f"Ошибка обработки: {str(e)}"})
                continue
            
            # Добавляем текущее сообщение пользователя
            messages.append(ttt.create_chat_message("user", user_input))
            print("Messages", messages)
            
            # Генерация ответа от агента
            response = await Runner.run(agent, messages)
            agent_text = response.final_output
            
            # Отправка ответа без истории, т.к. она хранится на фронтенде
            if is_audio == True:
                # Генерация аудио ответа
                print(f"persona_voice_tone_prompt: {prompts['persona_voice_tone_prompt']}")
                tts_response = tts.generate_speech(agent_text, tone=prompts["persona_voice_tone_prompt"])
                agent_audio = base64.b64encode(tts_response.content).decode('utf-8')
                
                # Отправка аудио и текста
                await ws.send_json({
                    "type": "voice",
                    "content": agent_text,
                    "user_text": user_input,
                    "audio": agent_audio
                })
            elif is_audio == False:
                # Отправка только текста
                await ws.send_json({
                    "type": "text",
                    "content": agent_text
                })
    except WebSocketDisconnect:
        pp("WebSocket disconnected")