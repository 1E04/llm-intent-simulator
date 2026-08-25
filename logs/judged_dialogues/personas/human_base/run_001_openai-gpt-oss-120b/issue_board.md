# 📊 Voice Bot QA Issue Board

---

## 🚨 Critical Security Alerts (CVSS 7.0 - 10.0)
**No critical vulnerabilities detected.**  
All failures are classification‑ or flow‑related; no prompt injection, data leakage, or agency‑overreach was observed.

---

## 🐞 High Priority Classification Bugs  

| Target Intent | Recurrent Mis‑Classification Pattern | Why It Happens (Judge Insight) | Recommended Fix |
|---------------|--------------------------------------|--------------------------------|-----------------|
| **card_acceptance** | Frequently swapped to **supported_cards_and_currencies** or **visa_or_mastercard** (7/8 dialogues). | The model treats “where can I use my card?” as a card‑feature query rather than a merchant‑acceptance query. | Create a distinct sub‑intent hierarchy: *card_acceptance → merchant_acceptance* vs *card_features*. Add training examples that contain “merchant”, “store”, “online” keywords paired with the correct label. |
| **virtual_card_not_working** | Often labeled **disposable_card_limits**, **declined_card_payment**, or **card_payment_not_recognised** (5/6 dialogues). | “Virtual” and “disposable” are lexically close; the model defaults to limit‑related intents. | Introduce a “virtual_card_issue” umbrella intent with explicit children: *not_working*, *limits*, *declined*. Provide contrastive examples where the problem is functional (fails to work) vs. limit‑related. |
| **pending_transfer** | Drifts to **transfer_timing** or **transfer_fee_charged** after the first turn (2/2 dialogues). | The model conflates “pending” with “when will it arrive”. | Strengthen the definition of *pending_transfer* with examples that include “still pending”, “not received yet”, and explicitly **not** asking about timing. |
| **transfer_fee_charged** | Switched to **pending_top_up**, **extra_charge_on_statement**, or kept asking for extra details (4/5 dialogues). | Fee‑related wording overlaps with “extra charge” and “pending” categories. | Add negative training pairs: “fee charged on transfer” → *transfer_fee_charged*; “extra charge on statement” → *extra_charge_on_statement*. Emphasize that fee queries should stay on the *transfer* domain. |
| **receiving_money** | Alternates with **transfer_into_account**, **supported_cards_and_currencies**, **fiat_currency_support** (3/4 dialogues). | The phrase “receive money” is interpreted as an internal transfer rather than inbound payments. | Enrich the intent with synonyms (“salary”, “incoming payment”, “deposit”) and add disambiguation prompts that ask “Are you looking to receive money from another bank or from a person?” |
| **exchange_via_app** | Starts correctly but falls back to **exchange_rate** (4/6 dialogues). | Users mention “exchange” → model defaults to rate lookup. | Separate *exchange_action* (perform exchange) from *exchange_info* (rate/fees). Use a rule‑based pre‑filter: if the user asks “how do I exchange” or “can I exchange”, force *exchange_via_app*. |
| **supported_cards_and_currencies** | Mis‑identified as **topping_up_by_card** or **top_up_failed** (1 dialogue). | Overlap of “supported cards” with top‑up methods. | Add clear negative examples where “supported cards” is asked without any top‑up context. |
| **verify_my_identity** | Often confused with **why_verify_identity** (2 dialogues). | Both belong to the verification family; the model picks the more common “why” variant. | Use a binary classifier for “process vs. reason” and add explicit training sentences for each. |
| **card_payment_not_recognised** | Mis‑labeled as **extra_charge_on_statement** (1 dialogue). | Both involve statement anomalies; the model picks the charge‑related intent. | Add contrastive examples: “I don’t recognise a payment” → *card_payment_not_recognised*; “I was charged extra” → *extra_charge_on_statement*. |
| **visa_or_mastercard** | Swapped with **country_support** (1 dialogue). | “Visa in Japan” triggers geographic reasoning. | Teach the model that “Visa or Mastercard?” is a *card_type* query, not a *country_support* query. |
| **balance_not_updated_after_bank_transfer** | Flips to **transfer_timing** or **pending_transfer** (2 dialogues). | “Balance not updated” is interpreted as a timing issue. | Provide examples where the problem is *balance not updated* and the correct label is *balance_not_updated_after_bank_transfer*. |
| **direct_debit_payment_not_recognised** | Starts as **card_payment_not_recognised** or **compromised_card** (2 dialogues). | “Payment not recognised” is generic; the model defaults to card‑payment domain. | Add explicit “direct debit” keyword cues and a separate intent for *direct_debit_not_recognised*. |
| **apple_pay_or_google_pay** | Mis‑identified as **topping_up_by_card** or **pending_top_up** (2 dialogues). | “Apple Pay” is seen as a top‑up method. | Create a dedicated *mobile_wallet* intent family and train with examples that mention Apple/Google Pay without top‑up context. |
| **order_physical_card** | Mixed with **card_arrival** or **card_delivery_estimate** (1 dialogue). | Delivery‑related wording causes confusion. | Distinguish *ordering* (fees, eligibility) from *delivery status* with clear lexical triggers. |
| **country_support** | Mixed with **order_physical_card** (1 dialogue). | “Country support” can be interpreted as “can I order a card in X?”. | Add disambiguation: if the user asks “Is X supported?” → *country_support*; if they say “I want to order” → *order_physical_card*. |
| **topping_up_by_card** | Often labeled as **top_up_reverted** (1 dialogue). | “Top‑up” + “failed” → model picks the more specific *reverted* label. | Strengthen the hierarchy: *topping_up_by_card* → *top_up_failed* → *top_up_reverted*. Use cascade logic to keep the broader intent when the user hasn’t indicated a reversal. |
| **cash_withdrawal_not_recognised** | Mis‑labeled as **lost_or_stolen_card** (1 dialogue). | Both involve security concerns. | Add clear negative examples: “I don’t recognise a cash withdrawal” → *cash_withdrawal_not_recognised*. |
| **get_pin** | Switched to **card_arrival** / **card_about_to_expire** (1 dialogue). | “PIN delivery” shares the word “card”. | Separate *pin_delivery* from *card_status* intents with distinct training data. |

**Overall Trend:** The bot often **starts with the correct intent** but **drifts** to a **semantically adjacent** intent in later turns. This indicates weak **context retention** and an over‑reliance on keyword matching rather than dialogue state.

**Suggested System‑Level Fixes**
1. **Intent State Tracker** – keep the first‑turn intent as the canonical label unless a high‑confidence re‑classification occurs.
2. **Hierarchical Intent Taxonomy** – group related intents (e.g., *card_acceptance* ↔ *supported_cards_and_currencies*) and enforce a “most‑specific‑match” rule.
3. **Contrastive Training** – for each pair of frequently confused intents, add explicit negative examples.
4. **Turn‑Level Confidence Threshold** – if confidence drops below a set threshold, ask a clarifying question *without* changing the stored intent label.
5. **Prompt‑Level Disambiguation** – prepend a short reminder of the current intent when asking follow‑ups (e.g., “Just to confirm, you’re asking about **card acceptance** …”).

---

## ⚠️ Persona Sensitivity Issues  
All failures involve the **HumanBase** persona; no alternative personas (e.g., non‑native speaker, senior, Gen‑Z) were present in the dataset. Consequently, no persona‑specific degradation is observed. Continue monitoring as new persona variants are introduced.

---

## 🔄 UX & Efficiency Flaws  

| Issue | Example(s) | Impact | Remedy |
|-------|------------|--------|--------|
| **Repeated Clarification after user already supplied info** | *transaction_charged_twice* (bot asks same confirmation repeatedly); *pending_card_payment* (asks for status & days again); *atm_support* (asks location twice). | Increases turn count, frustrates user, lowers efficiency scores. | Implement **slot‑filling memory**: once a slot is filled, do not request it again unless the user changes the answer. |
| **No final resolution / hand‑off** | *exchange_via_app*, *top_up_by_bank_transfer_charge*, *balance_not_updated_after_bank_transfer*, *atm_support*, *card_arrival*, *pending_cash_withdrawal*. | Goal achievement remains low despite correct intent detection. | Add a **conversation closure policy** that, after required info is gathered, either provides the answer or escalates to a human/FAQ link. |
| **Long clarification chains for simple queries** | *exchange_charge* (5 turns for a simple discount question); *top_up_failed* (multiple turns before fee info). | Redundant steps waste time. | Use **short‑circuit rules**: if the user asks a direct “what is the fee?” and provides currency/amount, answer immediately without extra probing. |
| **Switching intents mid‑dialogue without user clarification** | *card_acceptance*, *virtual_card_not_working*, *failed_transfer*, *exchange_via_app*. | Breaks conversational coherence, leads to ambiguous intent scores. | Enforce **intent persistence** (see above) and only switch on explicit user re‑statement. |
| **Missing actionable next steps** | *reverted_card_payment* (no confirmation of refund status); *unable_to_verify_identity* (only asks for details, never offers troubleshooting); *pending_top_up* (no resolution). | Users are left without a clear path forward. | Append a **standard “next steps” template** based on intent (e.g., “We’ll investigate and get back within 24 h”, or “You can reset your passcode here: …”). |
| **Over‑asking for already‑known data** | *pending_card_payment* (asks for country after user gave days & status); *exchange_via_app* (asks for rate again after user supplied amount). | Redundant, reduces perceived competence. | Ensure **slot de‑duplication** and **contextual awareness** across turns. |

---

### Quick Wins
- **Cache filled slots** across the dialogue.
- **Add a “confirm intent” step** after the first turn for ambiguous queries, then lock the intent.
- **Introduce intent‑specific answer templates** to guarantee a final response (even if it’s a hand‑off).
- **Fine‑tune on a balanced set of confused intent pairs** identified above.

--- 

*Prepared by the QA Architecture team – Senior AI Tech Lead*