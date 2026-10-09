import pytest
from unittest.mock import MagicMock
from app.services.llm_agent import LLMAgent, check_irrelevant_query


@pytest.fixture
def agent():
    a = LLMAgent()
    a.client = MagicMock()
    return a


def test_check_irrelevant_query_detection():
    # Irrelevant queries should return a topic descriptor
    assert check_irrelevant_query("write python code to reverse a string") == "coding and software development"
    assert check_irrelevant_query("create a java class for binary search") == "coding and software development"
    assert check_irrelevant_query("solve 2x + 15 = 45") == "mathematics and academic homework"
    assert check_irrelevant_query("who is the prime minister of india") == "politics and world affairs"
    assert check_irrelevant_query("should I invest in bitcoin cryptocurrency") == "financial and investment advice"
    assert check_irrelevant_query("who was napoleon") == "general trivia and world history"
    assert check_irrelevant_query("what is the capital of france") == "general trivia and world history"
    assert check_irrelevant_query("please give me medical advice for fever") == "medical or legal consultations"


def test_check_relevant_food_queries_not_blocked():
    # Food, grocery, and concierge queries should NEVER be marked irrelevant
    assert check_irrelevant_query("add 1 meghana chicken biryani") is None
    assert check_irrelevant_query("order amul milk and bread") is None
    assert check_irrelevant_query("what is on the menu") is None
    assert check_irrelevant_query("is there spicy chicken starter") is None
    assert check_irrelevant_query("open food cart") is None
    assert check_irrelevant_query("where is my delivery rider") is None
    assert check_irrelevant_query("track my order") is None
    assert check_irrelevant_query("hello") is None
    assert check_irrelevant_query("who are you") is None
    assert check_irrelevant_query("what can you do") is None


@pytest.mark.asyncio
async def test_agent_politely_declines_irrelevant_questions(agent):
    irrelevant_prompts = [
        "write python code to sort an array",
        "solve 3x + 10 = 25",
        "who will win the political election",
        "should I buy bitcoin crypto today",
        "who was napoleon",
    ]

    for prompt in irrelevant_prompts:
        res = await agent.process_user_message(user_phone="+919876543210", text_message=prompt)
        reply = res.get("reply", "")
        # Must politely state dedication to food orders / Instamart groceries
        assert "dedicated" in reply.lower() or "not dedicated" in reply.lower()
        assert "food" in reply.lower() or "groceries" in reply.lower()
        assert res.get("order") is None
