import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase
from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
import json

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent

load_dotenv(dotenv_path=project_root / ".env")
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

driver = GraphDatabase.driver(
    "neo4j://localhost:7687", auth=("neo4j", "passw0rd")
)

# Note: Verify the exact Groq model ID in your Groq console (e.g., "qwen/qwen3-32b" or "llama-3.3-70b-versatile")
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=800,
)


def run(query, **params):
    with driver.session() as session:
        return [r.data() for r in session.run(query, **params)]


# ---------- Tools (decorated with @tool so LangChain can bind and run them) ----------
@tool
def get_next_concepts(student_id: str) -> list[dict]:
    """Concepts the student is ready to learn next, based on prerequisite mastery."""
    rows = run("""
        MATCH (s:Student {id:$sid})-[:ENROLLED_IN]->(:Course)-[:HAS_UNIT]->(:Unit)-[:HAS_CONCEPT]->(c:Concept)
        OPTIONAL MATCH (s)-[m:MASTERY]->(c)
        WITH s, c, coalesce(m.score, 0) AS score
        WHERE score < 0.7 AND NOT EXISTS {
          MATCH (p:Concept)-[:PREREQUISITE_OF]->(c)
          WHERE NOT EXISTS { MATCH (s)-[pm:MASTERY]->(p) WHERE pm.score >= 0.7 }
        }
        RETURN c.id AS id, c.name AS name, score ORDER BY c.difficulty LIMIT 5
    """, sid=student_id)
    if not rows:
        return json.dumps({"message": "No eligible next concepts found for this student.", "concepts": []})
    return json.dumps(rows, default=str)


@tool
def find_prerequisite_gaps(student_id: str, concept_id: str) -> list[dict]:
    """Weak prerequisite concepts that may explain why a student struggles with a concept."""
    rows = run("""
        MATCH (s:Student {id:$sid})
        MATCH (:Concept {id:$cid})<-[:PREREQUISITE_OF*1..3]-(p:Concept)
        OPTIONAL MATCH (s)-[m:MASTERY]->(p)
        WITH p, coalesce(m.score, 0) AS score WHERE score < 0.7
        RETURN p.id AS id, p.name AS name, score
    """, sid=student_id, cid=concept_id)
    if not rows:
        return json.dumps({"message": "No prerequisite gaps found.", "gaps": []})
    return json.dumps(rows, default=str)


@tool
def record_answer(student_id: str, concept_id: str, correct: bool) -> dict:
    """Record whether the student answered a question on a concept correctly."""
    return run("""
        MATCH (s:Student {id:$sid}), (c:Concept {id:$cid})
        MERGE (s)-[m:MASTERY]->(c)
        ON CREATE SET m.score = 0.0
        SET m.score = round(0.7 * m.score + 0.3 * $val, 3), m.updated = datetime()
    """, sid=student_id, cid=concept_id, val=1.0 if correct else 0.0)
    return json.dumps({"status": "recorded"})


TOOLS = [get_next_concepts, find_prerequisite_gaps, record_answer]

SYSTEM = """You are a patient school tutor. Use the tools to check what the student
is ready for and to diagnose gaps before explaining. Explain at the student's grade
level, use short steps and examples, and ask one practice question at a time.
Never reveal other students' data. Stay on the school curriculum."""

# Pass TOOLS directly (not [TOOLS])
agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt=SYSTEM,
)


# ---------- Simplified Agent Invocation ----------
def chat(student_id: str, user_message: str, history=None):
    messages = list(history or []) + [
        {"role": "user",
            "content": f"[student_id={student_id}] {user_message}"}
    ]

    # create_agent runs the tool loop automatically and returns the full message history
    result = agent.invoke({"messages": messages})
    updated_messages = result["messages"]
    final_reply = updated_messages[-1].content
    return final_reply, updated_messages


if __name__ == "__main__":
    reply, _ = chat("S001", "I don't understand graphing lines. Help!")
    print(reply)
