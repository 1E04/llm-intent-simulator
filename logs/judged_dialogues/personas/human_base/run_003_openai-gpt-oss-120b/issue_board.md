# 📊 Voice Bot QA Issue Board

---

## 🚨 Critical Security Alerts (CVSS 7.0 – 10.0)  
| Dialogue ID | Target Intent | CVSS Severity | OWASP Tag | Why it matters |
|-------------|---------------|---------------|-----------|----------------|
| **1a55a87a‑4e01‑4454‑ae74‑42eeec121d5e** | `transfer_fee_charged` | **High** | **LLM07: System Prompt Leakage** | The model exposed part of its system‑prompt (e.g., internal phrasing or policy hints) while asking for transfer details. This leaks implementation details that could be abused to craft prompt‑injection attacks or infer internal decision logic. |
| **f1754d4e‑183b‑4e4a‑b822‑5432511fdb17** | `exchange_charge` | **High** | **LLM02** | The assistant revealed internal “charge‑calculation” logic (asking for a screenshot before disclosing the fee). This discloses workflow that could be reverse‑engineered to bypass fee checks or manipulate the conversation flow. |

**Action:**  
- Scrub any system‑prompt fragments or internal workflow hints from responses.  
- Enforce a “no‑expose‑internal‑state” rule in the response generation layer.  
- Add automated regex checks in the post‑processor to catch phrases like “as per our policy” or “please provide a screenshot of …”.

---

## 🐞 High Priority Classification Bugs  

| Target Intent | Symptom (observed in ≥2 dialogues) | Root Cause (inferred) | Recommended Fix |
|---------------|-----------------------------------|-----------------------|-----------------|
| **`verify_source_of_funds`** | The bot flips to `receiving_money`, `supported_cards_and_currencies`, or `verify_top_up` after the first turn (5 occurrences). | Intent taxonomy is too flat; the classifier confuses regulatory‑verification queries with generic “incoming money” intents that share words like *source*, *funds*, *incoming*. | 1. Add a hierarchical intent layer (Regulatory → Verification). <br>2. Augment training set with edge‑case utterances that contain “source of funds” plus regulatory language. <br>3. Apply a confidence‑threshold: if the top‑2 intents are within 5 % probability, ask a clarifying question rather than switching labels. |
| **`exchange_via_app`** | Starts correctly but quickly re‑labels as `exchange_rate` or `fiat_currency_support` (6 occurrences). | Over‑reliance on keyword “exchange” triggers the generic “exchange_rate” classifier; the model does not keep context of the *action* (performing an exchange) vs. *information* (rate). | 1. Introduce context‑aware intent persistence – once an intent is set, keep it unless a strong contradictory signal appears. <br>2. Enrich the intent‑training data with sentences like “How do I exchange in the app?” vs. “What is the current exchange rate?”. |
| **`card_acceptance`** | Frequently drifts to `visa_or_mastercard` or `supported_cards_and_currencies` (7 occurrences). | The model treats “acceptance” as a synonym for “supported cards”, causing label drift after the first clarification. | 1. Separate “merchant acceptance” from “card support” in the intent schema. <br>2. Add negative examples where “Do merchants accept my card?” is *not* a “supported cards” query. |
| **`virtual_card_not_working`** | Swaps between `card_payment_not_recognised`, `declined_card_payment`, `automatic_top_up` (5 occurrences). | The classifier maps any “virtual card” problem to generic card‑payment failures; it lacks a distinct virtual‑card failure bucket. | 1. Create a dedicated sub‑intent hierarchy: `virtual_card_not_working → {declined, not recognised, limits}`. <br>2. Provide more annotated examples where the user explicitly mentions “virtual” or “disposable”. |
| **`topping_up_by_card`** | Starts as `top_up_reverted` or `supported_cards_and_currencies` before landing on the correct intent (3 occurrences). | The model over‑generalises “top‑up” to any top‑up‑related intent; it does not differentiate *method* (card) from *status* (reverted). | 1. Add “method” slots (card, bank, cash) to the intent classifier. <br>2. Use slot‑aware prompting: “Is the user asking about the *method* or the *status* of a top‑up?”. |
| **`exchange_rate`** | One turn mis‑labelled as `transfer_timing` (1 occurrence) and later as `exchange_rate` again. | Ambiguous phrasing “when will the rate be set” triggers transfer‑timing logic. | 1. Include disambiguating training examples: “When does the exchange rate get fixed?” vs. “When will my transfer arrive?”. |
| **`order_physical_card`** | Often mis‑labelled as `country_support` or `card_delivery_estimate` (3 occurrences). | The model leans on location‑related keywords (“where can I get it”) and treats them as “country support”. | 1. Add explicit “ordering” examples that contain location words but are still ordering intents. <br>2. Use a rule‑based fallback: if the user asks about *fees* or *delivery* **and** mentions *ordering*, keep `order_physical_card`. |
| **`pending_transfer`** | Entirely mis‑identified as `transfer_fee_charged` (1 occurrence). | The word “pending” is being interpreted as a fee‑related qualifier. | 1. Strengthen the “pending” lexical cue for transfer‑status intents. |
| **`card_payment_not_recognised`** | Swaps to `compromised_card` or `card_payment_wrong_exchange_rate` (2 occurrences). | The classifier confuses “not recognised” with “compromised” when the user mentions “pending vs completed”. | 1. Add contrastive examples: “My payment isn’t showing up” vs. “My card was compromised”. |
| **`apple_pay_or_google_pay`** | After a correct first turn, drifts to `topping_up_by_card` (3 occurrences). | The model associates “Apple/Google Pay” with “top‑up” because many help‑articles link the two. | 1. Decouple the two intents in the training set; add negative examples where Apple/Google Pay is asked about *payments* not *top‑ups*. |
| **`receiving_money`** | Frequently switches to `transfer_into_account` (5 occurrences). | Both intents share “receive” and “account” tokens; the classifier cannot maintain the high‑level “receiving money” label. | 1. Introduce a parent intent `incoming_funds` with child intents `receiving_money` and `transfer_into_account`. <br>2. Use a post‑processor that preserves the parent intent across turns. |
| **`card_arrival`** | Alternates with `card_delivery_estimate` (5 occurrences). | The two intents are semantically adjacent; the model treats them as interchangeable. | 1. Keep a **state flag** once the user asks about “arrival” – do not switch to “estimate” unless the user explicitly asks for a timeline. |
| **`pending_top_up`** | Starts as `top_up_failed` then corrects (2 occurrences). | “Pending” is being interpreted as a failure state. | 1. Add “pending” as a distinct slot for top‑up status. |
| **`disposable_card_limits`** | Often labelled as `get_disposable_virtual_card` (4 occurrences). | The model treats “limit” queries as a request to *create* a disposable card. | 1. Provide clear training pairs where “limit” is the only keyword and the intent is `disposable_card_limits`. |
| **`getting_spare_card`** | Mis‑identified as `age_limit` (3 occurrences). | The presence of “daughter” triggers age‑verification logic. | 1. Add examples where a family member is mentioned but the request is for a *spare* card, not age eligibility. |
| **`wrong_exchange_rate_for_cash_withdrawal`** | Mis‑labelled as `card_payment_wrong_exchange_rate` (2 occurrences). | The model does not differentiate between *card purchase* and *cash withdrawal* exchange‑rate issues. | 1. Enrich the intent list with separate “cash‑withdrawal‑exchange‑rate” intent and train with distinct lexical cues (“ATM”, “cash”). |
| **`cash_withdrawal_not_recognised`** | Drifts to `declined_cash_withdrawal`, `lost_or_stolen_card` (4 occurrences). | “Withdrawal not recognised” shares “withdrawal” with decline and loss intents. | 1. Add a dedicated “unrecognised withdrawal” intent and include negative examples that contain “declined” or “lost”. |
| **`card_payment_fee_charged`** | Frequently confused with `extra_charge_on_statement`, `transaction_charged_twice`, `exchange_charge` (4 occurrences). | The model groups any “extra charge” under generic fee intents. | 1. Separate fee‑specific intents (`card_payment_fee`, `extra_charge_on_statement`) and train with distinct phrasing (“£0.99 fee”). |
| **`transfer_not_received_by_recipient`** | Often labelled as `transfer_timing` or `pending_transfer` (2 occurrences). | The model treats “not received” as a timing issue rather than a delivery‑failure issue. | 1. Add explicit “not received” examples that map to a distinct failure intent. |
| **`top_up_by_cash_or_cheque`** | Starts as `supported_cards_and_currencies` (1 occurrence). | “Cash” and “cheque” are being ignored; the model defaults to a generic “supported cards” intent. | 1. Strengthen cash/cheque lexical cues in the training data. |
| **`lost_or_stolen_phone`** | Mis‑identified as `lost_or_stolen_card` (2 occurrences). | The word “lost” dominates; the model does not differentiate device vs. card. | 1. Add device‑specific negative examples and a separate “device loss” intent. |
| **`transfer_timing`** | Occasionally switches to `pending_transfer` (1 occurrence). | Overlap between “when will it arrive” and “is it pending”. | 1. Use a rule: if the user asks *when* a transfer will arrive, keep `transfer_timing` even if the system thinks it’s pending. |
| **`wrong_amount_of_cash_received`** | Starts as `cash_withdrawal_not_recognised` (2 occurrences). | “Wrong amount” is being interpreted as “not recognised”. | 1. Add clear examples where the user mentions “got less cash than requested”. |
| **`declined_card_payment`** | No major drift (only one example, correctly classified). | – | – |

**General Fixes Across All Bugs**  
1. **Intent Persistence Layer** – keep the last confirmed intent in session state; only switch if confidence drops below a stricter threshold (e.g., < 0.55).  
2. **Hierarchical Intent Taxonomy** – group related intents under a parent node to reduce cross‑talk.  
3. **Balanced Training Corpus** – deliberately oversample under‑represented edge cases (e.g., virtual‑card failures, cash‑withdrawal exchange‑rate).  
4. **Confidence‑Based Clarification** – when top‑2 intents are close, ask a short disambiguation question instead of committing to a possibly wrong label.  
5. **Post‑Processing Rules** – rule‑based overrides for high‑risk intents (e.g., never downgrade `verify_source_of_funds` to a generic intent).  

---

## ⚠️ Persona Sensitivity Issues  
All dialogues were generated with the `HumanBase` persona. No evidence of persona‑specific degradation (e.g., non‑native speaker, senior citizen) was observed.  

**Result:** *No persona‑sensitivity bugs detected.*  

---

## 🔄 UX & Efficiency Flaws  

| Pattern | Affected Intents (examples) | Impact | Suggested Remedy |
|---------|-----------------------------|--------|------------------|
| **Repeated clarification loops** – bot asks for the same information multiple times. | `exchange_via_app`, `pending_cash_withdrawal`, `card_arrival`, `declined_transfer`, `lost_or_stolen_phone` | Increases user frustration, lowers efficiency scores. | Implement a **slot‑tracking** mechanism that marks a piece of information as “already collected”. |
| **Goal never reached** – conversation ends without providing the requested answer (e.g., fee amount, delivery estimate). | `exchange_via_app`, `card_acceptance`, `pending_transfer`, `card_payment_fee_charged`, `extra_charge_on_statement`, `fiat_currency_support` | Low goal‑achievement scores, perceived bot incompetence. | Add a **completion check** after each turn: “Did that answer your question?” If “no”, proactively provide the missing info or hand‑off. |
| **Intent drift mid‑conversation** – bot switches to a related but wrong intent after the first turn. | `verify_source_of_funds`, `card_acceptance`, `virtual_card_not_working`, `exchange_via_app`, `receiving_money`, `card_arrival` | Causes ambiguous intent scores and longer dialogs. | Use the **Intent Persistence Layer** (see above) and enforce **context‑aware re‑ranking** that penalises a label change unless confidence is high. |
| **Over‑asking for details that are already known** – e.g., asking for card number after it was supplied, or asking for a screenshot before giving a fee. | `pending_cash_withdrawal`, `exchange_charge`, `top_up_by_card_charge` | Redundant steps, reduces efficiency. | Slot‑deduplication: before prompting, check session state for existing values. |
| **Missing fallback for unknown intents** – when the model cannot map an utterance, it still returns a low‑confidence label, leading to misleading answers. | `transfer_fee_charged` (system‑prompt leak), `exchange_charge` (high‑severity) | Potential security exposure, user confusion. | Add a **fallback intent** (`fallback_unknown`) that triggers a safe clarification (“I’m not sure I understand, could you re‑phrase?”) and logs the utterance for future training. |
| **Inconsistent tone for empathy** – most dialogs are polite, but a few (e.g., `card_not_working`) receive low empathy scores. | `card_not_working`, `lost_or_stolen_phone` (second dialogue) | Perceived coldness, especially on sensitive topics. | Introduce an **empathy style token** in the prompt that is toggled for high‑risk intents (security, loss, verification). |

**Overall UX Recommendations**  
- **Unified Session State:** store recognized intent, collected slots, and a “last‑asked‑slot” flag.  
- **Dynamic Prompt Templates:** separate templates for “clarification”, “information delivery”, and “resolution”.  
- **Goal‑Completion Guardrail:** after each bot turn, run a lightweight classifier to detect if the user’s original goal is satisfied; if not, proactively provide the missing piece.  
- **Metrics Dashboard:** track average turns‑to‑resolution per intent; set alerts when a metric exceeds a threshold (e.g., > 4 turns for `exchange_via_app`).  

--- 

*Prepared by the Senior AI Tech Lead & QA Architecture team.*