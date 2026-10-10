"""AI 助手 —— 对话编排：规则检索为底座，可选 DeepSeek 润色。"""

from app.modules.assistant import llm, rules


def _facts(result: dict) -> str:
    lines = [str(result.get("reply", ""))]
    for item in result.get("data", []) or []:
        lines.append(f"{item.get('label')}：{item.get('value')}")
    table = result.get("table")
    if table and table.get("rows"):
        lines.append(" | ".join(table.get("columns", [])))
        for row in table["rows"][:20]:
            lines.append(" | ".join(str(c) for c in row))
    return "\n".join(lines)


def chat(db, user, message: str) -> dict:
    result = rules.answer(db, user, message)
    result.setdefault("mode", "rules")
    if llm.enabled() and result.get("reply"):
        polished = llm.polish(message, _facts(result))
        if polished:
            result["reply"] = polished
            result["mode"] = "llm"
    return result
