# Property Inquiry Extractor

A Python script that reads a raw WhatsApp property inquiry and extracts five fields as JSON, so a Nairobi property agent no longer has to copy details into a spreadsheet by hand.

## The problem

A property agent in Nairobi receives WhatsApp messages like:

> "I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month"
>
> "Do you have any bedsitters near Westlands under 20k?"

She reads each message and types the details into a spreadsheet. This is slow, and typing mistakes creep in. This script does the reading and sorting automatically.

## What the script does

1. Takes a raw inquiry message as input.
2. Sends it to the Gemini API together with a structured **system prompt** (the standing instructions) and **few-shot examples** (solved samples the model copies).
3. Receives the reply as JSON and parses it into a Python dictionary.
4. Checks the result: missing keys are filled with `null`, and a budget that is not a number triggers a warning.
5. Prints each field cleanly. Missing information is shown as "Not stated".

## Fields extracted

| Field | Example | Why it matters |
|---|---|---|
| `property_type` | house, bedsitter | Decides which listings to show the client. A bedsitter client should not be shown maisonettes. |
| `bedrooms` | 3 (a bedsitter is 0) | Filters listings by size. Stored as a number so it can be sorted and filtered. |
| `location` | Kileleshwa | Matches the client to the right area. Location is usually the first thing a client cares about. |
| `budget_kes` | 80000 | Filters listings by price. Stored as a plain number in Kenyan shillings so it can be compared and sorted ("80k" becomes 80000). |
| `rental_or_sale` | rental | Rentals and sales are different deals with different listings and different commissions. |

## Rules the prompt follows

These rules are the "business rulebook". They live in the system prompt and can be changed to match how a particular agent works.

- **Missing information is `null`.** The model must not guess. A wrong value in a spreadsheet looks like a fact, so a blank is safer.
- `property_type` is one of: house, apartment, bedsitter, studio, maisonette, other. A bedroom count or a location alone does not reveal the type, so it is not inferred.
- A **bedsitter has 0 bedrooms**.
- Budget shorthand is converted: "80k" becomes 80000 and "25M" becomes 25000000.
- "Under 20k" uses 20000. For a range such as "30-40k", the **higher** number is used.
- "Near Westlands" gives the location "Westlands".
- `rental_or_sale` is only filled when the message gives a clear clue (for example "rent", "per month", "buy"). Otherwise it is `null`.
- The reply must be JSON only, with all five keys always present.

## How it works

| Part of `extractor.py` | Purpose |
|---|---|
| `SYSTEM_PROMPT` | Role, task, field rules and output rules |
| `FEW_SHOT_EXAMPLES` | Six solved examples, including a message with no information and a partial message |
| `get_ai_reply(message)` | Sends one message to the model and returns the reply text |
| `parse_reply(reply_text)` | Converts the JSON text into a dictionary and checks it |
| `print_inquiry(data)` | Prints the five fields cleanly |
| `TEST_MESSAGES` | The list of messages used to test the script |

The request also asks the API for a JSON reply (`response_mime_type="application/json"`), which adds a second layer of protection on top of the prompt.

## Setup

**You need:** Python 3.10 or newer, and a free Gemini API key from [Google AI Studio](https://aistudio.google.com).

1. Clone the repository and open the folder:

   ```bash
   git clone https://github.com/mujuniegid-hue/Property-Inquiry-Extractor.git
   cd property-inquiry-extractor
   ```

2. Create and activate a virtual environment:

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Mac / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the libraries:

   ```bash
   pip install -r requirements.txt
   ```

4. Create a file named `.env` in the project folder containing:

   ```
   GEMINI_API_KEY=your-key-here
   ```

   The `.env` file is listed in `.gitignore` and must never be uploaded.

5. Check the `MODEL_NAME` value near the top of the code. Model names change over time. If you get a "model not found" error, use `list_models.py` (if included) or the AI Studio documentation to find a current name.

## Usage

Run the script:

```bash
python extractor.py
```

It runs every message in `TEST_MESSAGES`. To try your own message, add it to that list, or set a single `message = "..."` and call the functions directly.

### Example output

```
TEST 1: I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month
--------------------------------
Property type : house
Bedrooms      : 3
Location      : Kileleshwa
Budget (KES)  : 80,000
Rent or sale  : rental
--------------------------------
```

## Test results

Five different messages were tested, including one with missing information. Results can vary slightly between runs because AI models are not perfectly consistent.

| # | Message | Extracted result |
|---|---|---|
| 1 | "I am looking for a 3-bedroom house in Kileleshwa, budget around 80k per month" | house, 3, Kileleshwa, 80,000, rental |
| 2 | "Do you have any bedsitters near Westlands under 20k?" | bedsitter, 0, Westlands, 20,000, not stated |
| 3 | "Looking to buy a 3 bedroom in Karen, budget 25M" | not stated, 3, Karen, 25,000,000, sale |
| 4 | "Is the place still available? Please call me." (**missing information**) | all fields not stated |
| 5 | "Looking for a 1 bedroom in Parklands, 30-40k a month" | not stated, 1, Parklands, 40,000, rental |

### What testing taught me

- **A rule alone did not stop the model from guessing.** In test 3, the model first returned "house" for "3 bedroom in Karen" even though the type was never stated. Adding an explicit rule and a matching few-shot example fixed it.
- **Examples can override rules.** In test 2, the model first answered "rental" because one of my few-shot examples contradicted my own rule. Correcting the example fixed it. Examples must always agree with the rules.
- **Test messages should not appear in the examples**, otherwise the test proves nothing. The examples use different areas from the test messages.

## Limitations

- Accuracy depends on the AI model, and results can vary between runs.
- Messages written in Swahili or in a mix of languages have not been tested properly.
- For a budget range, only the higher number is kept.
- The script reads one message at a time and prints the result. It does not yet write to a spreadsheet or connect to WhatsApp.
- It relies on a free-tier API, which can be slow and has usage limits. A client-ready version would use a paid, reliable service, retry failed requests, and store results.
- Whether the model should infer details (for example, assuming a bedsitter is a rental) is a business decision for the agent. The current rulebook is deliberately strict.

## Possible next steps

- Save extracted results to a CSV file or Google Sheet.
- Process a whole file of messages in one run.
- Add Swahili examples to the prompt and test them.
- Connect to WhatsApp Business so messages arrive automatically.

## Security

- The API key is stored in `.env`, never in the code.
- `.env`, `venv/` and `__pycache__/` are listed in `.gitignore`.
- If a key is ever uploaded by mistake, delete it in Google AI Studio immediately and create a new one.

## Built with

- Python
- Google Gemini API (`google-genai`)
- `python-dotenv`