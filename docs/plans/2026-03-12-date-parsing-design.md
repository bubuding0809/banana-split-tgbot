# Personal Expense Date Parsing Enhancement Design

**Date:** 2026-03-12
**Topic:** Integrating `dateparser` for advanced relative date support in personal expenses

## 1. Overview
The bot currently supports parsing expenses from free text (e.g., `15 USD Lunch`). However, date parsing is rigidly limited to `YYYY-MM-DD` and the exact word `yesterday`. The user wants to support natural, relative dates (e.g., `2 days ago`, `last friday`).

We will integrate the `dateparser` Python library to parse these dates natively.

## 2. Architecture & Libraries
- Add `dateparser` to `requirements.txt`.
- Import `dateparser` in `handlers/user_handlers.py`.

## 3. Parsing Logic (`parse_expense`)
To balance convenience with robustness and prevent false positives (where parts of the expense description are mistakenly parsed as dates), we will implement a hybrid approach:

### Approach: Delimiter-Based parsing with Single-Word Fallback
1. **Explicit Delimiter (Comma):**
   - The user can explicitly separate the date using a comma `,` at the end of their message.
   - Example: `15 USD Lunch with friends, 2 days ago`
   - Logic: 
     - Check if the text contains a `,`. 
     - If yes, split by the *last* comma. 
     - Attempt to parse the right side using `dateparser.parse()`. 
     - If successful, the left side is tokenized normally for amount/currency/description.
     - If parsing fails, the comma is treated as part of the description and we fall back to tokenization.

2. **Single-Word Parsing (Fallback):**
   - If no comma is present (or comma parsing fails), we split the text into space-separated tokens as we currently do.
   - For each token, we check if it is a valid date.
   - To prevent false positives on common description words, single-word parsing will be restricted to:
     - Strict formats like `YYYY-MM-DD`.
     - A specific set of safe relative words/days (e.g., `today`, `yesterday`, `monday`, `tuesday`, etc.).

## 4. Date Normalization
- All parsed dates from `dateparser` must be forced to midnight (`00:00:00`) and assigned the `timezone.utc` timezone to remain consistent with existing backend storage assumptions for daily expenses.
- Future dates will be allowed (as they are currently), relying on the backend to accept them.

## 5. UI & Documentation Updates
- Update `messages.py`:
  - `USAGE_GUIDE`: Add a brief example of the comma syntax (e.g., `15 USD Lunch, 2 days ago`).
  - `EXPENSE_PARSE_HINT`: Add an example showing the comma syntax.
