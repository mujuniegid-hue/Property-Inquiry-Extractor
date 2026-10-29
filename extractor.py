import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json

SYSTEM_PROMPT = """
You are a data-extraction assistant for a property agent in Nairobi, Kenya.
You will receive one raw WhatsApp inquiry from a potential client.
Extract the following five fields and return them as JSON.

FIELDS AND RULES:
- property_type: one of "house", "apartment", "bedsitter", "studio",
  "maisonette", "other". Use null if not stated.A bedroom count or a
  location alone does NOT tell you the type, so do not infer it.
- bedrooms: a whole number. A bedsitter is 0. Use null if not stated.
- location: the neighbourhood or area name, e.g. "Kileleshwa".
  For "near Westlands", use "Westlands". Use null if not stated.
- budget_kes: a number in Kenyan shillings, with no commas or text.
  Convert shorthand: "80k" = 80000, "1.5M" = 1500000.
  For "under 20k", use 20000. For a range like "60-80k", use the higher number.
  Use null if no budget is given.
- rental_or_sale: "rental" or "sale". Use "rental" if the message mentions
  rent, monthly payments, or "per month". Use "sale" if it mentions buying
  or purchasing. If unclear, use null. Do not guess.

OUTPUT RULES:
- Return ONLY valid JSON. No explanation, no extra text, no markdown fences.
- Always include all five keys, even when the value is null.
- Never invent information that is not in the message.
"""

FEW_SHOT_EXAMPLES = """
EXAMPLES:

Message: "Hello, I need a 2 bedroom apartment in Lavington for rent, around 90k monthly"
{"property_type": "apartment", "bedrooms": 2, "location": "Lavington", "budget_kes": 90000, "rental_or_sale": "rental"}

Message: "Looking for a bedsitter in Roysambu, not more than 10k"
{"property_type": "bedsitter", "bedrooms": 0, "location": "Roysambu", "budget_kes": 10000, "rental_or_sale": "null"}

Message: "We want to buy a 4 bedroom maisonette in Runda, up to 45M"
{"property_type": "maisonette", "bedrooms": 4, "location": "Runda", "budget_kes": 45000000, "rental_or_sale": "sale"}

Message: "Hi, are there any places available?"
{"property_type": null, "bedrooms": null, "location": null, "budget_kes": null, "rental_or_sale": null}

Message: "Do you have anything in Ruaka? Need 3 bedrooms"
{"property_type": null, "bedrooms": 3, "location": "Ruaka", "budget_kes": null, "rental_or_sale": null}
Message: "Need a 3 bedroom in Syokimau for rent, 35k"
{"property_type": null, "bedrooms": 3, "location": "Syokimau", "budget_kes": 35000, "rental_or_sale": "rental"}
"""

SYSTEM_PROMPT = SYSTEM_PROMPT + FEW_SHOT_EXAMPLES

load_dotenv()

client = genai.Client(http_options=types.HttpOptions(timeout=60000))

MODEL_NAME = "gemini-3.1-flash-lite"   # use the name that worked for you

EXPECTED_KEYS = ["property_type", "bedrooms", "location", "budget_kes", "rental_or_sale"]


def get_ai_reply(message):
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
        ),
    )
    return response.text


def parse_reply(reply_text):
    try:
        data = json.loads(reply_text)
    except json.JSONDecodeError:
        print("Could not read the AI's reply as JSON. Raw reply was:")
        print(reply_text)
        return None

    for key in EXPECTED_KEYS:
        if key not in data:
            data[key] = None

    budget = data["budget_kes"]
    if budget is not None and not isinstance(budget, (int, float)):
        print(f"Warning: budget_kes is not a number: {budget!r}")

    return data


def show(value):
    if value is None:
        return "Not stated"
    return value


def print_inquiry(data):
    print("-" * 32)
    print(f"Property type : {show(data['property_type'])}")
    print(f"Bedrooms      : {show(data['bedrooms'])}")
    print(f"Location      : {show(data['location'])}")
    if data["budget_kes"] is None:
        print("Budget (KES)  : Not stated")
    else:
        print(f"Budget (KES)  : {data['budget_kes']:,}")
    print(f"Rent or sale  : {show(data['rental_or_sale'])}")
    print("-" * 32)


TEST_MESSAGES = [
    "I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month",
    "Do you have any bedsitters near Westlands under 20k?",
    "Looking to buy a 3 bedroom in Karen, budget 25M",
    "Is the place still available? Please call me.",
    "Looking for a 1 bedroom in Parklands, 30-40k a month",
]

for number, message in enumerate(TEST_MESSAGES, start=1):
    print(f"TEST {number}: {message}")
    reply = get_ai_reply(message)
    data = parse_reply(reply)
    if data is not None:
        print_inquiry(data)
    print()