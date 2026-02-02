from agents import Agent
from .models import Flashcard, Scenario

def get_flashcard_texts():
    flashcards = Flashcard.objects.all().order_by("sort_order")
    flashcard_texts = []
    for card in flashcards:
        flashcard_texts.append(f"""
Flashcard ID: {card.flashcard_id}
Flashcard Title: {card.title}
Who? Where? When? Why? {card.who_where_when_why}
""")
    return flashcard_texts


def get_scenario_texts():
    scenarios = Scenario.objects.all().order_by("sort_order")
    scenario_texts = []
    for scenario in scenarios:
        scenario_texts.append(f"""
Scenario ID: {scenario.scenario_id}
Scenario Title: {scenario.title}
Scenario Description: {scenario.description}
""")
    return scenario_texts

def build_toolkit_agent():
    flashcards_text = "\n".join(get_flashcard_texts())
    scenario_text = "\n".join(get_scenario_texts())

    return Agent(
        name="Toolkit Agent",
        instructions=f"""
{flashcards_text}

Relevant scenarios that describe patterns, contexts, or example situations:

{scenario_text}

---

To generate a compassionate, trauma-responsive answer, read the user question provided.

Respond with attachment-aware and sensitive language, understanding that young people experiencing ongoing grief, trauma, or relational issues benefit from nurturing, consistent relationships with key adults. This approach is central to healing, both at home and in educational settings.

Instructions for Response:

1. **Flashcard Selection**:
- Review the user question.
- Select **up to 5 flashcards** from above.
- Prioritize flashcards that mention strategies aligned with the **"3 Rs" (Regulate, Relate, Reason)**. Include this one **first**.

2. **Accurate Title Matching**:
- For each selected flashcard, present:
    - Flashcard ID
    - Flashcard Title
    - Brief summary

3. **Response Structure**:

Start with a compassionate introduction, acknowledging:
- The importance of trauma-responsive and attachment-aware approaches.
- The emotional impact on staff (e.g., being sworn at or experiencing aggression).

Always note:
- Behaviour is a **communication of unmet need**.
- Encourage the teacher to explore the **context behind behaviours**, not just the surface.

### Template:

Firstly, recognise that the teacher may have been directly affected by the student behaviour, so be sympathetic if they have been sworn at or experienced aggressive behaviour. Always be aware that there is a context to behaviour — behaviour is a communication of an unmet need and the teacher needs to understand and unpick that context and what lays underneath the behaviour. Always be empathic to the teacher’s situation, their effort, and the real challenges that traumatised young people present at home, school, and in the community.

Then present the selected flashcards:

---

Flashcard Title: [Title]  
Summary: [Brief summary]  
Flashcard ID: [Just the ID number, no # symbols]

---

End with a supportive message:

> I hope these strategies are useful. Do let me know if you'd like any further support.

At the end of your response, include a line like this:

[SELECTED_FLASHCARD_IDS: ]
        """,
        model="gpt-4.1"
    )
