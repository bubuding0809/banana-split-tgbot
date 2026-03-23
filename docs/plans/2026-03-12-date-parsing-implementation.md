# Personal Expense Date Parsing Integration

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enhance the Telegram bot's expense parser to natively support flexible, relative date patterns using `dateparser` while preventing false positives.

**Architecture:** We will introduce a two-tier parsing approach in `user_handlers.py`: a delimiter-based check (comma `,`) that safely passes the trailing string to `dateparser`, and a single-word fallback loop that uses `dateparser` only for strict date/day words. We will enforce UTC midnight normalisation.

**Tech Stack:** Python 3.11, `dateparser` library.

---

### Task 1: Install Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Install `dateparser`**
Run: `./venv/bin/pip install dateparser`
Expected: Installation succeeds.

**Step 2: Update `requirements.txt`**
Run: `./venv/bin/pip freeze > requirements.txt`
Expected: `dateparser` and its dependencies are added to `requirements.txt`.

**Step 3: Commit**
```bash
git add requirements.txt
git commit -m "chore: add dateparser dependency"
```

---

### Task 2: Refactor `parse_expense` logic

**Files:**
- Modify: `handlers/user_handlers.py`

**Step 1: Import dateparser and tz**
At the top of `user_handlers.py`, add the `dateparser` import and update datetime imports if needed:
```python
import dateparser
from datetime import datetime, timezone
```

**Step 2: Add single-word date whitelist**
Inside `UserCommandHandler` class, add a class-level frozen set of safe single words to allow fast fallback checking:
```python
_SAFE_SINGLE_DATES = frozenset([
    "yesterday", "today", "tomorrow", "monday", "tuesday", 
    "wednesday", "thursday", "friday", "saturday", "sunday",
    "mon", "tue", "wed", "thu", "fri", "sat", "sun"
])
```

**Step 3: Update `parse_expense` to support the comma delimiter**
At the beginning of the `parse_expense` method (around line 275), insert the delimiter logic before tokenizing the input:
```python
        text = text.strip()
        if not text:
            return None

        amount: Optional[float] = None
        currency: Optional[str] = None
        date: Optional[datetime] = None
        desc_parts: list[str] = []
        
        # 1. Delimiter-Based Parsing
        # Check if the user provided a comma to explicitly separate the date
        if "," in text:
            # Split by the last comma
            parts = text.rsplit(",", 1)
            left_side = parts[0].strip()
            right_side = parts[1].strip()
            
            # Attempt to parse the right side as a date
            parsed_date = dateparser.parse(right_side)
            if parsed_date:
                # Normalise to UTC midnight
                date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=timezone.utc)
                else:
                    date = date.astimezone(timezone.utc)
                
                # Treat the left side as the remaining text to tokenize
                text = left_side

        # 2. Tokenize the remaining text
        tokens = text.split()
```

**Step 4: Update the single-word token loop**
Replace the old `yesterday` and `_DATE_RE` logic inside the `for token in tokens:` loop (around line 302) with `dateparser` and the whitelist:
```python
            # Try date
            if date is None:
                token_lower = token.lower()
                # Only use dateparser for tokens if they match exact YYYY-MM-DD or our safe whitelist
                if UserCommandHandler._DATE_RE.match(token) or token_lower in UserCommandHandler._SAFE_SINGLE_DATES:
                    parsed_date = dateparser.parse(token)
                    if parsed_date:
                        date = parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        if date.tzinfo is None:
                            date = date.replace(tzinfo=timezone.utc)
                        else:
                            date = date.astimezone(timezone.utc)
                        continue
```

**Step 5: Verify syntax**
Run: `./venv/bin/python -m py_compile handlers/user_handlers.py`
Expected: Silent output (no syntax errors).

**Step 6: Commit**
```bash
git add handlers/user_handlers.py
git commit -m "feat: integrate dateparser for advanced date extraction"
```

---

### Task 3: Update documentation and templates

**Files:**
- Modify: `messages.py`

**Step 1: Update usage templates**
In `messages.py`, find `EXPENSE_PARSE_HINT` and `USAGE_GUIDE`. Update the date examples to reflect the new capabilities:

```python
    EXPENSE_PARSE_HINT = (
        "💡 To log a personal expense, send a message like:\n"
        "  `12.50 Lunch`\n"
        "  `Grab ride 8.90`\n"
        "  `Coffee 5`\n"
        "  `25.50 Movie tickets, 2 days ago`"
    )

    USAGE_GUIDE = """
*Track Personal Expenses*: Send me a direct message\\! For example:
```
15 USD Lunch
```
```
30000 JPY Japanese whiskey
``` \\(Currency\\)
```
200 beer, last friday
``` \\(Date via comma\\)
```
12 Grab ride yesterday
``` \\(Simple Date\\)

*Commands:*
\\- `/list`: See your history
\\- `/stats`: See your spending summary

*Group Expenses:*
1\\. *Add me to a group chat*: Click the "Add to group" button below or go to your group chat and add me as a member\\.
2\\. *Start the bot*: Use the `/start@{bot_username}` command in the group chat to kick things off\\.
3\\. *Get your friends to join*: Have them open the mini\\-app in the group chat to split expenses\\.

🚀 Happy tracking and splitting\\! 🍌🍌🍌
"""
```

**Step 2: Verify syntax**
Run: `./venv/bin/python -m py_compile messages.py`
Expected: Silent output.

**Step 3: Commit**
```bash
git add messages.py
git commit -m "docs: update help templates with relative date patterns"
```
