# 📊 Voice Bot QA Issue Board

## 🚨 Critical Security Alerts (CVSS 7.0 - 10.0)
**No critical vulnerabilities detected.**  
All dialogues were evaluated as free of prompt injection, data leakage, or agency‑overreach issues.

---

## 🐞 High Priority Classification Bugs
| Target Intent | Symptom (Observed Across Multiple Dialogues) | Root Cause (Judge’s Insight) | Recommended Fix |
|---------------|---------------------------------------------|------------------------------|-----------------|
| **request_refund** | Bot flips to `card_payment_not_recognised` or `cancel_transfer` after an initial correct hit. | Intent classifier over‑generalises to “payment‑issue” family when a charge is mentioned. | Add a **hard rule**: if the user mentions “refund” or “money back”, force `request_refund` before any secondary classifier runs. |
| **Refund_not_showing_up** | Starts with `request_refund` then drifts to `request_refund` again or other refund‑related intents. | Ambiguous wording (“refund not showing”) triggers sibling intent mapping. | Enrich training data with “refund missing / pending” phrasing and increase weight on the “refund‑status” sub‑intent. |
| **card_acceptance** | Frequently mis‑labelled as `supported_cards_and_currencies`, `visa_or_mastercard`, or `country_support`. | Model treats “where can I use my card?” as a geographic‑currency query rather than merchant‑acceptance. | Create a **dedicated “card_acceptance” pattern set** (keywords: “accepted”, “merchant”, “use my card at”) and separate it from country‑support patterns. |
| **virtual_card_not_working** | Swaps to `disposable_card_limits`, `declined_card_payment`, or `automatic_top_up`. | Virtual‑card terminology overlaps with “disposable” and generic “decline” intents. | Introduce a **virtual‑card taxonomy** that distinguishes “not working” from “limits” and “declines”. Add negative‑example training (e.g., “my virtual card won’t work” → `virtual_card_not_working`). |
| **exchange_via_app** | Starts with correct intent but quickly reverts to `exchange_rate`. | “Exchange” keyword dominates classifier, drowning out “via app” cue. | Add a **contextual bias** for “via app / perform exchange” and include more examples where the user explicitly asks to *execute* an exchange. |
| **exchange_rate** | After correct detection, drifts to `exchange_charge` or `card_payment_wrong_exchange_rate`. | Over‑reliance on “rate” token leads to charge‑related intents. | Strengthen disambiguation rules: if the user asks “what is the rate?” → `exchange_rate`; if they ask “how much will I be charged?” → `exchange_charge`. |
| **pending_transfer / pending_top_up** | Starts correctly but later switches to `transfer_timing`, `transfer_fee_charged`, or `top_up_failed`. | The “pending” flag is treated as a temporal cue rather than a distinct intent. | Create a **pending‑state flag** that persists across turns once detected, preventing downstream drift. |
| **transfer_fee_charged** | Occasionally mis‑identified as `extra_charge_on_statement`. | Fee‑related language is shared across statement‑charge intents. | Add a **fee‑type hierarchy** where “transfer fee” outranks generic “extra charge” when the word “transfer” appears. |
| **card_arrival** | Swapped with `card_delivery_estimate`. | Both intents share “card” + “date” tokens; classifier cannot differentiate arrival status vs. estimate. | Separate the two by adding explicit trigger phrases: “has my card arrived?” → `card_arrival`; “when will my card be delivered?” → `card_delivery_estimate`. |
| **transaction_charged_twice** | Repeated confirmation questions after all details are supplied. | Dialogue manager lacks a **completion condition** for this intent. | Implement a **resolution step** that, after gathering required fields, either provides next‑step guidance or hands off to a human. |
| **apple_pay_or_google_pay** | Mis‑labelled as `topping_up_by_card` or `pending_top_up`. | “Pay” token is conflated with generic top‑up intents. | Add distinct lexical cues (`Apple Pay`, `Google Pay`, `mobile wallet`) to the intent lexicon. |
| **getting_spare_card** | Alternates between `order_physical_card` and `getting_spare_card`. | “Spare” is interpreted as a generic “order card” request. | Introduce a **spare‑card synonym list** and prioritize it over generic ordering. |
| **lost_or_stolen_phone** | Classified as `lost_or_stolen_card`. | “Lost” keyword triggers card‑loss intent regardless of device context. | Add device‑specific patterns (`phone`, `mobile`, `device`) and a rule to route to `lost_or_stolen_phone`. |
| **top_up_by_card_charge** | First turn mis‑labelled as `supported_cards_and_currencies`. | “Card” + “charge” triggers currency‑support intent. | Strengthen the “top‑up fee” pattern and add negative examples for currency‑support queries. |

*Action items*:  
1. **Retrain** the intent classifier with the enriched, negative‑example‑rich datasets above.  
2. **Introduce intent persistence flags** for “pending” and “failed” families to avoid drift.  
3. **Add rule‑based overrides** for high‑risk intents (refund, lost phone, transaction‑charged‑twice) to guarantee exact matches before ML scoring.

---

## ⚠️ Persona Sensitivity Issues
All failures involve the default `HumanBase` persona. No evidence of degraded performance for non‑native speakers, age‑specific personas, or other demographic variants.  
**Recommendation**: Continue monitoring as new personas are introduced; currently no persona‑specific remediation needed.

---

## 🔄 UX & Efficiency Flaws
| Issue | Typical Manifestation | Impact | Suggested Remedy |
|-------|----------------------|--------|------------------|
| **Repeated Clarification Loops** | Bot asks for the same detail (e.g., card type, amount, country) multiple times (seen in `card_acceptance`, `exchange_via_app`, `transaction_charged_twice`, `atm_support`). | Increases turn count, frustrates users, lowers efficiency scores. | Implement **state tracking** to remember already‑provided slots; add a “slot already filled” guard. |
| **Late Resolution / No Hand‑off** | Many dialogues end without a concrete answer or next‑step (e.g., `pending_transfer`, `transfer_fee_charged`, `balance_not_updated_after_bank_transfer`, `exchange_via_app`). | Goal‑achievement scores stay low despite polite conversation. | Define **completion criteria** per intent (e.g., provide fee amount, give status link, or trigger hand‑off to a human). |
| **Over‑Specific Sub‑Intent Switching** | Bot jumps from a broad correct intent to a narrower, unrelated sub‑intent (e.g., `card_acceptance` → `country_support`; `exchange_via_app` → `exchange_rate`). | Confuses users, reduces confidence in the bot’s understanding. | Use a **hierarchical intent model** where the parent intent persists unless a strong confidence boost for a child intent is observed. |
| **Redundant Confirmation Prompts** | After all required info is gathered, the bot still asks “Can you confirm …?” (e.g., `transaction_charged_twice`, `passcode_forgotten`). | Wastes turns and can be perceived as robotic. | Add a **post‑gathering branch** that directly proceeds to resolution or hand‑off. |
| **Missing Direct Answers** | Bot asks clarifying questions but never supplies the requested data (e.g., `exchange_charge` – asks about discount vs. rate repeatedly; `atm_support` – never returns ATM list). | Users never achieve their primary goal. | Ensure **answer generation** is triggered once all slots are filled; fallback to a knowledge‑base lookup before asking more questions. |
| **Inconsistent Intent Labels Within a Single Dialogue** | Same user request labeled differently across turns (e.g., `virtual_card_not_working`, `card_arrival`, `getting_spare_card`). | Lowers trust and hampers downstream analytics. | Enforce **intent consistency checks**: if the current intent differs from the previous turn without a user‑initiated topic change, flag for review or auto‑revert to the original intent. |

*Overall UX Recommendation*:  
- Deploy a **dialogue manager** that maintains a **slot‑filled map** and **intent persistence flag** across turns.  
- Add **confidence thresholds** that, when not met, trigger a clarification sub‑flow rather than a full intent switch.  
- Introduce **fallback hand‑off** after a configurable number of turns without resolution (e.g., 4‑5 turns).

---

### Summary of Immediate Priorities
1. **Fix high‑frequency mis‑classifications** (refund, card acceptance, virtual card, exchange via app).  
2. **Add intent persistence and slot memory** to stop repetitive questioning.  
3. **Define clear resolution endpoints** for each intent to improve goal‑achievement scores.  
4. **Implement rule‑based overrides** for critical intents (refund, lost phone, duplicate charge).  

Addressing these points should raise intent‑recognition scores toward 5, improve efficiency (target ≥ 4), and increase overall user satisfaction with the Banking Voice Bot.