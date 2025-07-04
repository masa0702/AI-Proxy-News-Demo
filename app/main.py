from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from . import data
import os

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def mock_gemini(prompt: str) -> str:
    """Placeholder for Gemini API call"""
    return f"[Gemini Response] {prompt}"[:200]


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
        generated_question = mock_gemini(
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
    article = mock_gemini(news_prompt)

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
