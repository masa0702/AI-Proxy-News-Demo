from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from . import data
import os

import google.generativeai as genai

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def gemini_api(prompt: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "[Gemini API KEYが設定されていません]"
    try:
        genai.configure(api_key=api_key)
        # 利用可能な最新モデルに変更（例: "models/gemini-1.5-pro-latest"）
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip() if hasattr(response, "text") else str(response)
    except Exception as e:
        return f"[Gemini APIエラー: {e}]"



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "topics": data.TOPICS,
            "biases": data.BIASES,
            "article": None,
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, topic_id: int = Form(...), bias_id: int = Form(...)):
    topic = data.get_topic(topic_id)
    bias = data.get_bias(bias_id)
    knowledge_list = data.get_knowledge(topic_id)
    knowledge_text = " ".join(k["text"] for k in knowledge_list)

    question_entry = data.get_question(topic_id)
    if question_entry:
        generated_question = gemini_api(
            f"{topic['topic']}に関する質問を{bias['bias']}の視点で1つ生成してください"
        )
        question = generated_question
        answer = question_entry["answer"]
    else:
        question = "質問がありません"
        answer = ""

    news_prompt = (
        f"トピック: {topic['topic']} バイアス: {bias['bias']} 知識: {knowledge_text} "
        f"質問: {question} 回答: {answer}。これらを基にニュース記事を書いてください。"
    )
    article = gemini_api(news_prompt)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "topics": data.TOPICS,
            "biases": data.BIASES,
            "article": article,
            "selected_topic": topic_id,
            "selected_bias": bias_id,
            "question": question,
            "answer": answer,
        },
    )
