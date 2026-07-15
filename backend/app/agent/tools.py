import os
from langchain_core.tools import tool
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from ..database import SessionLocal
from .. import models

load_dotenv()

# Fast, cheap model - used inside tools for extraction/summarization tasks
# llm = ChatGroq(model="gemma2-9b-it", api_key=os.getenv("GROQ_API_KEY")) // deprecated by Groq in favor of llama-3.1-8b-instant
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))


# ---------- TOOL 1: LOG INTERACTION (required) ----------
@tool
def log_interaction(hcp_name: str, raw_notes: str) -> str:
    """
    Logs a new HCP interaction. Takes the HCP's name and raw free-text notes
    (e.g. from a chat message like "Met Dr. Sharma, discussed OncoBoost efficacy,
    positive sentiment, shared brochure"). Uses the LLM to extract structured
    fields (topics discussed, sentiment, materials shared) from the raw text,
    then saves it to the database. Returns a confirmation with the new interaction ID.
    """
    db = SessionLocal()
    try:
        # Find or create the HCP
        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            hcp = models.HCP(name=hcp_name)
            db.add(hcp)
            db.commit()
            db.refresh(hcp)

        # Ask the LLM to extract structured fields from the raw notes
        extraction_prompt = f"""Extract the following from this HCP interaction note.
Reply in this exact format, one per line, no extra text:
TOPICS: <key discussion points>
SENTIMENT: <Positive, Neutral, or Negative>
MATERIALS: <any materials/samples mentioned, or "None">

Note: {raw_notes}"""

        response = llm.invoke(extraction_prompt)
        parsed = _parse_extraction(response.content)

        interaction = models.Interaction(
            hcp_id=hcp.id,
            topics_discussed=parsed.get("TOPICS", raw_notes),
            sentiment=parsed.get("SENTIMENT", "Neutral"),
            materials_shared=parsed.get("MATERIALS", "None"),
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        return f"Logged interaction #{interaction.id} with {hcp.name}. Sentiment: {interaction.sentiment}."
    finally:
        db.close()


def _parse_extraction(text: str) -> dict:
    """Small helper: turns the LLM's line-based output into a dict."""
    result = {}
    for line in text.strip().split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip().upper()] = value.strip()
    return result


# ---------- TOOL 2: EDIT INTERACTION (required) ----------
@tool
def edit_interaction(interaction_id: str, field: str, new_value: str) -> str:
    """
    Edits an existing logged interaction. Takes the interaction ID, the field
    name to change (e.g. "sentiment", "outcomes", "followup_actions"), and the
    new value. Returns a confirmation or an error if the interaction isn't found.
    """
    db = SessionLocal()
    try:
        try:
            interaction_id_int = int(interaction_id)
        except ValueError:
            return f"Invalid interaction ID: {interaction_id}"

        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id_int
        ).first()
        if not interaction:
            return f"No interaction found with ID {interaction_id_int}."

        if not hasattr(interaction, field):
            return f"Field '{field}' does not exist on interaction records."

        setattr(interaction, field, new_value)
        db.commit()
        return f"Interaction #{interaction_id_int} updated: {field} → {new_value}"
    finally:
        db.close()


# ---------- TOOL 3: DETECT ADVERSE EVENT (complex / differentiator) ----------
@tool
def detect_adverse_event(interaction_id: str, interaction_text: str) -> str:
    """
    Scans interaction text for any mention of patient side effects, adverse
    reactions, or safety concerns about a drug, and flags the corresponding
    interaction record in the database if found. This is a regulatory
    requirement in pharma - any adverse event mentioned to a rep must be
    flagged for pharmacovigilance review. Always call this with the ID of the
    interaction that was just logged, right after calling log_interaction.
    """
    detection_prompt = f"""You are a pharmacovigilance assistant. Read this HCP interaction note
and determine if it mentions any adverse event (patient side effect, safety
concern, or product complaint related to a drug).

Reply in this exact format:
DETECTED: <Yes or No>
SUMMARY: <one sentence summary of the adverse event, or "N/A" if none>

Note: {interaction_text}"""

    response = llm.invoke(detection_prompt)
    parsed = _parse_extraction(response.content)

    detected = parsed.get("DETECTED", "No").strip().lower() == "yes"
    summary = parsed.get("SUMMARY", "N/A")

    if detected:
        db = SessionLocal()
        try:
            try:
                interaction_id_int = int(interaction_id)
                interaction = db.query(models.Interaction).filter(
                    models.Interaction.id == interaction_id_int
                ).first()
                if interaction:
                    interaction.ae_flagged = True
                    interaction.ae_summary = summary
                    db.commit()
            except ValueError:
                pass  # couldn't parse ID, skip the DB write but still report the finding
        finally:
            db.close()
        return f"⚠️ ADVERSE EVENT DETECTED. Summary: {summary}. This has been flagged in the record for pharmacovigilance review within 24 hours."

    return "No adverse event detected in this interaction."

# ---------- TOOL 4: GET INTERACTION HISTORY (simple DB read) ----------
@tool
def get_interaction_history(hcp_name: str, limit: int = 5) -> str:
    """
    Retrieves the most recent logged interactions for a given HCP by name.
    Useful for giving the rep context before a new meeting (e.g. "what did we
    last discuss with Dr. Sharma?"). Returns a formatted summary of past interactions.
    """
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            return f"No HCP found matching '{hcp_name}'."

        interactions = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp.id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )

        if not interactions:
            return f"No past interactions found for {hcp.name}."

        summary_lines = [f"Past interactions with {hcp.name}:"]
        for i in interactions:
            date_str = i.interaction_date.strftime("%Y-%m-%d")
            summary_lines.append(
                f"- [{date_str}] {i.topics_discussed or 'No notes'} (Sentiment: {i.sentiment or 'N/A'})"
            )

        return "\n".join(summary_lines)
    finally:
        db.close()

# ---------- TOOL 5: FIND INTERACTION (for editing without knowing the ID) ----------
@tool
def find_interaction(hcp_name: str = "", keyword: str = "") -> str:
    """
    Searches logged interactions by HCP name and/or a keyword found in the
    topics/outcomes. Use this BEFORE calling edit_interaction whenever the user
    refers to an interaction by description rather than by exact ID (e.g.
    "the pricing meeting with Dr. Sharma", "that interaction", "the one about X").
    Returns a list of matching interactions with their ID, date, and sentiment
    so the correct one can be identified. If multiple matches are found, do NOT
    guess - list them and ask the user to clarify which one, referencing date
    and sentiment.
    """
    db = SessionLocal()
    try:
        query = db.query(models.Interaction)
        if hcp_name:
            hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{hcp_name}%")).first()
            if hcp:
                query = query.filter(models.Interaction.hcp_id == hcp.id)
        if keyword:
            query = query.filter(models.Interaction.topics_discussed.ilike(f"%{keyword}%"))

        results = query.order_by(models.Interaction.interaction_date.desc()).limit(10).all()

        if not results:
            return "No matching interactions found."

        lines = ["Matching interactions:"]
        for r in results:
            date_str = r.interaction_date.strftime("%Y-%m-%d %H:%M")
            lines.append(f"- ID {r.id} | [{date_str}] | {r.topics_discussed} | Sentiment: {r.sentiment}")
        return "\n".join(lines)
    finally:
        db.close()

# ---------- TOOL 6: SUGGEST FOLLOW-UPS (simple, single LLM call) ----------
@tool
def suggest_followups(interaction_text: str) -> str:
    """
    Given the notes from a logged interaction, suggests 2-3 concrete follow-up
    actions for the rep (e.g. scheduling a next meeting, sending materials,
    adding the HCP to a mailing list). Returns a short bulleted list.
    """
    prompt = f"""Based on this HCP interaction note, suggest 2-3 short, concrete
follow-up actions a pharma sales rep should take next. Keep each suggestion
under 10 words. Reply as a plain bulleted list, nothing else.

Note: {interaction_text}"""

    response = llm.invoke(prompt)
    return response.content.strip()


# ---------- Collect all tools for the agent ----------
all_tools = [
    log_interaction,
    edit_interaction,
    detect_adverse_event,
    get_interaction_history,
    find_interaction,
    suggest_followups,
]