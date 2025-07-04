import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / 'data'

def load_json(filename):
    path = DATA_DIR / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

TOPICS = load_json('topics.json')
KNOWLEDGE = load_json('knowledge.json')
QUESTIONS = load_json('questions.json')
BIASES = load_json('biases.json')


def get_topic(topic_id):
    return next((t for t in TOPICS if t['id'] == topic_id), None)


def get_knowledge(topic_id):
    return [k for k in KNOWLEDGE if k['topic_id'] == topic_id]


def get_question(topic_id):
    return next((q for q in QUESTIONS if q['topic_id'] == topic_id), None)


def get_bias(bias_id):
    return next((b for b in BIASES if b['id'] == bias_id), None)
