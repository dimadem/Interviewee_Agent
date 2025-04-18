from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import PyPDF2
import io
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Улучшенный промпт для анализа резюме по методике STAR
STAR_PROMPT = """Проведи краткий и точный анализ резюме, следуя структуре:

1️⃣ ПРОФИЛЬ (2-3 предложения)
• Роль и уровень специалиста
• Ключевая экспертиза
• Общий опыт в годах

2️⃣ ТОП-3 ДОСТИЖЕНИЯ
Для каждого:
[S] Контекст: бизнес-задача (1 строка)
[T] Цель: измеримый результат (1 строка)
[A] Действия: конкретные шаги (2-3 пункта)
[R] Результат: числа и метрики (1-2 строки)

3️⃣ ТЕХНИЧЕСКИЙ СТЕК
• Hard skills: ключевые технологии и уровень владения
• Soft skills: 2-3 главные компетенции
• Сертификации/образование (если релевантно)

4️⃣ ЭКСПЕРТНАЯ ОЦЕНКА
• 🟢 Сильные стороны (3 пункта)
• 🔴 Зоны роста (2 пункта)
• ⭐ Рекомендации (2-3 конкретных шага)

Важно:
- Используй только факты из резюме
- Пиши кратко и по существу
- Выделяй конкретные метрики
- Избегай общих фраз
- Форматируй текст для легкого чтения"""

@router.post("/api/resume-analysis")
async def analyze_resume(resume: UploadFile = File(...)):
    if not resume.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Поддерживаются только PDF файлы")
    
    try:
        # Чтение PDF файла
        contents = await resume.read()
        pdf_file = io.BytesIO(contents)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Извлечение текста из PDF
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        # Используем более быструю модель GPT-3.5-turbo-1106
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": STAR_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=1200,
            presence_penalty=0.1,
            frequency_penalty=0.2
        )
        
        analysis = response.choices[0].message.content
        
        return JSONResponse(content={"analysis": analysis})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при анализе резюме: {str(e)}") 