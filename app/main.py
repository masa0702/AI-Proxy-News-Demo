from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import time, json, threading, os, random
from pathlib import Path
from . import data
import google.generativeai as genai

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

progress_data = {
    "message": [],
    "progress": 0,
    "question": "",
    "answer": "",
    "article": "",
}
progress_lock = threading.Lock()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'
TOPIC_TEXT_DIR = DATA_DIR / 'topics'
KNOWLEDGE_TEXT_DIR = DATA_DIR / 'knowldges'
QUESTION_JSON_PATH = DATA_DIR / 'questions.json'

def read_txt_file(path):
    if Path(path).exists():
        with open(path, encoding='utf-8') as f:
            return f.read().strip()
    return ""

def load_questions():
    if QUESTION_JSON_PATH.exists():
        with open(QUESTION_JSON_PATH, encoding='utf-8') as f:
            return json.load(f)
    else:
        return []

def save_questions(questions):
    with open(QUESTION_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

def gemini_api(prompt: str, temperature: float = 0.5) -> str:
    if not GEMINI_API_KEY:
        return "[Gemini API KEYが設定されていません]"
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content(prompt, generation_config={"temperature": temperature})
        return response.text.strip() if hasattr(response, "text") else str(response)
    except Exception as e:
        return f"[Gemini APIエラー: {e}]"

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "topics": data.TOPICS,
        "biases": data.BIASES,
    })

@app.post("/start_generate")
async def start_generate(request: Request, background_tasks: BackgroundTasks):
    req = await request.json()
    topic_id = int(req.get("topic_id"))
    bias_id = int(req.get("bias_id"))
    background_tasks.add_task(run_generation, topic_id, bias_id)
    return {}

def run_generation(topic_id, bias_id):
    global progress_data
    with progress_lock:
        progress_data = {"message": [], "progress": 0, "question": "", "answer": "", "article": ""}

    topic = data.get_topic(topic_id)
    bias = data.get_bias(bias_id)
    knowledge_list = data.get_knowledge(topic_id)
    knowledge_names = ", ".join([k["text"] for k in knowledge_list])

    # topic_n.txt, knowldge_n.txt の読み込み
    topic_txt = read_txt_file(TOPIC_TEXT_DIR / f"topic_{topic_id}.txt")
    knowldge_txt = read_txt_file(KNOWLEDGE_TEXT_DIR / f"knowldge_{topic_id}.txt")

    steps = [
        (f"ユーザーがトピック <strong>{topic['topic']}</strong> とバイアス <strong>{bias['bias']}</strong> を選択しました。", 5),
        (f"トピックに関する詳細情報を参照中…", 10),
        (f"詳細情報読込完了：<strong>{(topic_txt[:24] + '…') if topic_txt else '（詳細情報なし）'}</strong>", 15),
        (f"前提知識情報を参照中…", 20),
        (f"前提知識読込完了：<strong>{(knowldge_txt[:24] + '…') if knowldge_txt else '（知識情報なし）'}</strong>", 30),
        ("AIが質問を生成中…", 40),
        ("質問生成完了", 50),
        ("模範回答を取得中…", 65),
        ("模範回答取得完了", 70),
        ("記事生成中…", 80),
        ("記事生成完了", 100),
    ]

    question_prompt = (
        f"【トピック】\n{topic['topic']}\n"
        f"【詳細情報】\n{topic_txt}\n"
        f"【前提知識】\n{knowldge_txt}\n"
        f"この内容について、{bias['bias']}の視点で1つ質問を生成してください。"
    )

    question = ""
    answer = ""
    article = ""

    for i, (msg, prog) in enumerate(steps):
        if "AIが質問を生成中" in msg:
            time.sleep(1.0)
            with progress_lock:
                progress_data["message"].append(msg)
                progress_data["progress"] = prog
            # Gemini APIで質問生成
            question = gemini_api(question_prompt, temperature=0.0).strip()
            with progress_lock:
                progress_data["question"] = question

            # ▼▼ 質問の保存・answer取得ロジック ▼▼
            questions_data = load_questions()
            matched = next((q for q in questions_data if q["topic_id"] == topic_id and q["question"] == question), None)
            if matched and matched.get("answer"):
                answer = matched["answer"]
            else:
                # まだ未登録なのでquestion.jsonに保存
                if not matched:
                    questions_data.append({"topic_id": topic_id, "question": question, "answer": ""})
                    save_questions(questions_data)
                # 同じtopic_idのanswerからランダム取得（空文字は除く）
                candidates = [q["answer"] for q in questions_data if q["topic_id"] == topic_id and q.get("answer")]
                answer = random.choice(candidates) if candidates else ""
            with progress_lock:
                progress_data["answer"] = answer

        elif "質問生成完了" in msg:
            time.sleep(0.5)
            with progress_lock:
                progress_data["message"].append(f"質問生成完了：<strong>{question}</strong>")
                progress_data["progress"] = prog
        elif "模範回答を取得中" in msg:
            time.sleep(0.5)
            with progress_lock:
                progress_data["message"].append(msg)
                progress_data["progress"] = prog
        elif "模範回答取得完了" in msg:
            time.sleep(0.5)
            with progress_lock:
                progress_data["message"].append(f"模範回答取得完了：<strong>{answer}</strong>")
                progress_data["progress"] = prog
                progress_data["answer"] = answer
        elif "記事生成中" in msg:
            time.sleep(1.0)
            with progress_lock:
                progress_data["message"].append(msg)
                progress_data["progress"] = prog
                progress_data["article"] = "（AIが記事を生成中です…）"
            news_prompt = (
                f"【トピック】\n{topic['topic']}\n"
                f"【詳細情報】\n{topic_txt}\n"
                f"【前提知識】\n{knowldge_txt}\n"
                f"【質問】\n{question}\n"
                f"【回答】\n{answer}\n"
                "これら全てをふまえて、一般読者向けに分かりやすいニュース記事を書いてください。"
            )
            article = gemini_api(news_prompt, temperature=0.5)
            with progress_lock:
                progress_data["article"] = article
        elif "記事生成完了" in msg:
            time.sleep(0.5)
            with progress_lock:
                progress_data["message"].append(msg)
                progress_data["progress"] = prog
        else:
            time.sleep(1.0)
            with progress_lock:
                progress_data["message"].append(msg)
                progress_data["progress"] = prog

@app.get('/progress_stream')
async def progress_stream():
    def event_generator():
        last_index = 0
        while True:
            with progress_lock:
                msgs = progress_data["message"]
                prog = progress_data["progress"]
                q = progress_data.get("question", "")
                a = progress_data.get("answer", "")
                art = progress_data.get("article", "")
            if len(msgs) > last_index:
                msg = msgs[last_index]
                yield f'data: {json.dumps({"message":msg, "progress":prog, "question":q, "answer":a, "article":art})}\n\n'
                last_index += 1
            if prog >= 100:
                break
            time.sleep(0.3)
    return StreamingResponse(event_generator(), media_type='text/event-stream')
