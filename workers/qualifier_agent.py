def qualification_suggestions(intent: str):
    if intent == "interested":
        return [
            "Are you optimizing for velocity, cost efficiency, or both this quarter?",
            "Would you be open to a scoped pilot that can scale into a 12+ month pod?",
        ]
    return []
