# 📊 Voice Bot QA Issue Board  

---

## 🚨 Critical Security Alerts (CVSS 7.0 – 10.0)  
- **No critical CVSS‑rated vulnerabilities detected.**  
- **Potentially high‑impact behavior:**  
  - *Excessive Agency* – The bot sometimes takes actions (e.g., “freeze your card”) without explicit user confirmation (e.g., **card_payment_not_recognised** – LLM06).  
  - *Recommendation:* Add a mandatory confirmation step before any irreversible operation (card freeze, account termination, fund transfer cancellation).

---

## 🐞 High‑Priority Classification Bugs  

| Target Intent | Recurrent Mis‑classifications | Pattern / Root Cause | Suggested Fix |
|---------------|------------------------------|----------------------|---------------|
| **get_pin** | `card_payment_not_recognised`, `pin_blocked`, `change_pin` | PIN‑related intents are clustered together; the model defaults to the most frequent sibling. | Introduce more distinct training examples for `get_pin` vs. `pin_blocked`/`change_pin`; add a “PIN retrieval” keyword list (e.g., “forgot my PIN”, “need my PIN”). |
| **top_up_by_cash_or_cheque** | `top_up_failed`, `balance_not_updated_after_cheque_or_cash_deposit` | Cash‑top‑up and failure intents share many lexical cues (“cash”, “cheque”). | Separate feature space: add explicit “type of top‑up” tags; use hierarchical intent detection (first detect “top‑up by cash/cheque”, then “status”). |
| **card_arrival** | `card_delivery_estimate` | Both involve delivery timing; the model treats them as interchangeable. | Add disambiguating examples (e.g., “has my card arrived?” vs. “when will it be delivered?”) and enforce exact‑match scoring for delivery‑related intents. |
| **card_payment_not_recognised** | `compromised_card` (first turn) | Fraud‑related intents are highly correlated; the model jumps to the most severe label. | Prioritize `card_payment_not_recognised` when the user explicitly mentions “unknown charge” and only fallback to fraud after additional cues. |
| **contactless_not_working** | `declined_card_payment` (first two turns) | Contactless failures are a subset of declined payments; the model over‑generalises. | Add a “contactless” keyword bucket; train the model to keep the original intent once “contactless” is detected. |
| **supported_cards_and_currencies** | `declined_card_payment` | The model confuses “supported” with “declined” when the user mentions “card” and “currency”. | Provide clear negative examples where “supported” is asked; reinforce the “information request” pattern. |
| **card_not_working** | `declined_card_payment` | Broad “card problem” queries default to decline. | Separate “card not working” from “declined payment” with distinct dialogue flows and example sets. |
| **apple_pay_or_google_pay** | `declined_card_payment`, `card_payment_not_recognised` | Mobile‑wallet issues are treated as generic card declines. | Add dedicated training data for mobile‑wallet intents; include synonyms (“Apple Pay”, “Google Pay”, “mobile wallet”). |
| **automatic_top_up** | `compromised_card` (turn 5) | Fraud detection overrides automatic‑top‑up when suspicious language appears. | Use a two‑stage classifier: first detect “automatic top‑up”, then flag fraud only if explicit fraud cues are present. |
| **pending_transfer** | `balance_not_updated_after_bank_transfer`, `transfer_not_received_by_recipient` | Multiple “pending” intents cause label flipping. | Consolidate “pending” intents under a single umbrella with sub‑type slots; enforce consistency across turns. |
| **verify_my_identity** | `why_verify_identity` | The bot confuses “why” vs. “how”. | Add intent‑specific prompts: if user asks “why”, map to `why_verify_identity`; if they ask “how”, map to `verify_my_identity`. |
| **transfer_timing** | `transfer_not_received_by_recipient`, `pending_transfer` | Timing questions are interpreted as missing transfers. | Explicitly train the model on timing‑only queries (“when will it arrive?”) and separate from “not received”. |
| **cancel_transfer** | Correct intent but repeats confirmation step | Over‑cautious confirmation leads to extra turn. | Streamline flow: after first confirmation, proceed directly to cancellation. |
| **beneficiary_not_allowed** | `declined_transfer` | Specific decline reason not captured. | Add fine‑grained decline sub‑intents (e.g., “beneficiary not allowed”) with clear lexical triggers. |
| **order_physical_card** | `lost_or_stolen_card` | Replacement requests are conflated with loss reports. | Distinguish “order new card” vs. “report lost/stolen” via keyword sets (“replace”, “new card”). |
| **get_disposable_virtual_card** | `declined_card_payment`, `card_payment_not_recognised` | Virtual‑card requests default to generic payment issues. | Enrich training data with “disposable virtual card” phrasing; prioritize virtual‑card intents when “disposable” is present. |
| **verify_source_of_funds** | `unable_to_verify_identity` | Both involve verification, leading to cross‑talk. | Separate “source‑of‑funds verification” from “identity verification” with distinct slot names and examples. |
| **pending_card_payment** | `declined_card_payment` (first turn) | Pending holds are mis‑read as declines. | Add explicit “pending” language (“still pending”, “hold”) to training set; keep intent stable after first detection. |
| **cash_withdrawal_charge** | `exchange_charge` (first turn) | Fee‑related intents overlap. | Use domain‑specific cue words (“withdrawal”, “ATM”) to steer toward cash‑withdrawal fee intent. |
| **card_linking** | `card_not_working` (first turn) | Linking is seen as a generic card issue. | Provide linking‑specific examples (“link my card to the app”) and enforce early intent lock‑in. |

---

## ⚠️ Persona Sensitivity Issues  

| Persona | Observed Weakness | Impact | Mitigation |
|---------|-------------------|--------|------------|
| **Gen‑Z Slang** | Bot replies stay formal; low mirroring of slang; intent often mis‑detected (e.g., `get_pin`, `card_arrival`). | Reduces naturalness/empathy scores (3‑4) and may cause user disengagement. | Add a “style‑transfer” layer that injects slang when `persona=Gen‑Z`; augment training data with slang‑rich utterances. |
| **Non‑Native Speaker** | Frequent mis‑classifications (`card_acceptance`, `direct_debit_payment_not_recognised`, `verify_source_of_funds`). | Lower intent accuracy (2‑3) and higher clarification loops. | Include more multilingual/low‑proficiency examples; use simplified language detection to trigger clarification. |
| **Panicking Emergency** | Bot often fails to de‑escalate; uses polite tone but not calming; mis‑labels intents (`pending_transfer`, `card_payment_not_recognised`). | Empathy scores 2‑4; user may feel ignored in urgent situations. | Implement an “emergency‑mode” that prioritizes rapid confirmation, explicit reassurance, and fast‑track to resolution. |
| **Angry Layperson** | Empathy present but not strong enough; intent sometimes drifted (`card_payment_not_recognised`, `reverted_card_payment`). | Goal achievement suffers; conversation may prolong. | Add sentiment‑aware response templates that acknowledge anger and provide concise next steps. |
| **Polite Expert** | Generally high naturalness/empathy, but occasional intent drift (`why_verify_identity` → `verify_my_identity`). | Minor efficiency loss. | Keep intent lock‑in after first correct detection for expert personas. |
| **Short Wording** | Bot often jumps to the most common intent, ignoring brevity cues (`card_payment_not_recognised`, `transfer_timing`). | Leads to extra clarification turns. | Train on terse utterances; use a “short‑input” heuristic to broaden intent candidates before final selection. |

---

## 🔄 UX & Efficiency Flaws  

- **Intent flipping mid‑dialogue** – Many flows (e.g., `pending_transfer`, `card_arrival`, `automatic_top_up`) switch between two or more intents, causing user confusion and extra turns.  
  *Fix:* Once an intent is identified with confidence > 0.85, lock it for the remainder of the session unless the user explicitly changes the topic.  

- **Repeated clarification loops** – The bot often asks the same type of question multiple times (e.g., `exchange_via_app`, `top_up_failed`).  
  *Fix:* Cache already‑provided slot values and reuse them; add a “has‑already‑asked” guard.  

- **Missing resolution or hand‑off** – Numerous dialogues end without a concrete next step (e.g., `extra_charge_on_statement`, `verify_top_up`, `card_payment_not_recognised`).  
  *Fix:* Enforce a “closure” rule: after the final required slot is filled, always provide a summary, next‑step, or escalation option.  

- **Over‑cautious confirmation** – `cancel_transfer` repeats confirmation, adding an unnecessary turn.  
  *Fix:* Combine confirmation and execution in a single concise response when confidence is high.  

- **Lack of de‑escalation for high‑stress personas** – Panicking or angry users receive polite but not calming language.  
  *Fix:* Insert empathy scripts (“I understand this is frustrating; let’s resolve it quickly”) early in the flow for those sentiment tags.  

- **Inconsistent handling of “why” vs. “how” questions** – `why_verify_identity` often switches to `verify_my_identity`.  
  *Fix:* Detect question type (why/how) early and route to the correct intent without switching.  

- **Insufficient domain‑specific keyword coverage** – Several intents (e.g., `supported_cards_and_currencies`, `cash_withdrawal_charge`) are mis‑routed to generic payment‑decline intents.  
  *Fix:* Expand the lexical dictionary with domain‑specific terms (e.g., “supported”, “currency”, “ATM fee”) and weight them higher in the classifier.  

---

### Summary  

The Voice Bot shows solid language quality but suffers from systematic intent‑recognition ambiguities, especially when intents share overlapping terminology. Persona‑aware language generation is under‑utilized, leading to lower naturalness for Gen‑Z, non‑native, and high‑stress users. UX inefficiencies stem from intent flipping, repeated clarifications, and missing closure steps.  

**Priority actions:**  

1. **Re‑train the intent classifier** with hierarchical labeling and enriched keyword sets for the most error‑prone intents.  
2. **Implement intent lock‑in** and slot caching to stop mid‑dialogue flipping.  
3. **Add persona‑driven response styles** (slang injection, empathy escalation).  
4. **Introduce mandatory confirmation and closure steps** for irreversible actions and unresolved queries.  

Addressing these points will raise intent‑recognition accuracy, improve user satisfaction across personas, and eliminate the most common UX bottlenecks.