# 📊 Voice Bot QA Issue Board  

---

## 🚨 Critical Security Alerts (CVSS 7.0 – 10.0)  
**No critical vulnerabilities detected.**  
*All failures are functional/UX‑related; no prompt injection, data leakage, or agency‑overreach was observed.*

---

## 🐞 High Priority Classification Bugs  

| Target Intent | Recurrent Mis‑Classifications | Typical Pattern / Root Cause | Suggested Fix |
|---------------|--------------------------------|------------------------------|---------------|
| **card_payment_fee_charged** | `extra_charge_on_statement`, `exchange_charge`, `card_payment_not_recognised` | The model tends to gravitate toward any “fee‑related” label, even when the fee is specific to a card payment. | Add **fine‑grained training examples** that contrast card‑payment fees vs. generic extra‑charge scenarios; enforce a **hierarchical intent map** where `card_payment_fee_charged` is a sibling, not a parent, of `extra_charge_on_statement`. |
| **card_not_working** | `declined_card_payment` (sub‑intent drift) | The model treats “not working” as a subset of “declined”, losing the broader diagnostic context. | Introduce **negative examples** where a card is not working for reasons other than decline (e.g., offline, damaged) and map them explicitly to `card_not_working`. |
| **virtual_card_not_working** | `disposable_card_limits`, `declined_card_payment`, `card_payment_not_recognised` | Over‑generalisation to any “virtual‑card” sub‑category; the intent hierarchy is too shallow. | Create a **dedicated intent branch** for virtual‑card issues and train with **cross‑intent contrastive pairs** (virtual vs. disposable vs. declined). |
| **pending_transfer** | `transfer_timing`, `transfer_not_received_by_recipient`, `transfer_fee_charged` | The model confuses “pending” with “timing” or “not received”, indicating ambiguous label semantics. | Refine the **definition** of “pending” in the taxonomy and add **dialogue‑level cues** (e.g., user mentions “still pending”) to the training set. |
| **top_up_by_card** | `receiving_money`, `top_up_reverted`, `top_up_failed` | The model often interprets “can a friend top‑up me?” as a *receiving* problem rather than a *method* problem. | Provide **scenario‑based examples** where the user asks about third‑party top‑ups, emphasizing the *method* dimension. |
| **order_physical_card** | `card_payment_fee_charged`, `card_delivery_estimate`, `card_about_to_expire` | No correct prediction in any turn – the intent is completely missed. | **Add missing intent** to the training corpus; ensure the utterance patterns (“I want a new card”, “order a physical card”) are well represented. |
| **declined_transfer** | `failed_transfer` (later turn) | The model swaps “declined” ↔ “failed”, treating them as interchangeable. | Clarify the **semantic distinction** in the intent schema and inject **contrastive examples** (declined = rejected instantly, failed = could not be processed). |
| **cancel_transfer** | `failed_transfer`, `transfer_not_received_by_recipient` | After the first correct turn the bot drifts to unrelated transfer failure intents. | Anchor the **dialogue state** to the original intent and add **state‑preservation checks** before re‑classifying. |
| **request_refund** | `card_payment_wrong_exchange_rate` | The model jumps to a completely unrelated domain (exchange rate) when the user mentions “refund”. | Enrich the **refund‑related utterances** and add **negative sampling** for exchange‑rate queries. |
| **change_pin** | `get_pin`, `passcode_forgotten` | The model confuses “changing” with “retrieving/forgetting”. | Separate **PIN lifecycle intents** (retrieve, change, reset) with clear lexical cues in training data. |
| **disposable_card_limits** | `get_disposable_virtual_card` (or vice‑versa) | Intent overlap between “limits” and “how to get” a disposable card. | Introduce **explicit disambiguation prompts** and **dual‑label training** where the model must ask a clarification before committing. |
| **exchange_via_app** | `exchange_rate`, `supported_cards_and_currencies` | The model treats any currency‑related request as “exchange”, missing the “via app” procedural nuance. | Add **procedure‑focused examples** (step‑by‑step) and tag them with a **sub‑intent** `exchange_via_app_procedure`. |
| **atm_support** | Over‑asking (location → method → fee‑free) before delivering the ATM list | The model seeks excessive detail before answering the core request. | Implement a **short‑circuit rule**: once the primary slot (user location) is filled, provide the answer immediately. |
| **country_support** | Repeated clarification on “issuance vs usage” | The model never proceeds to the list of supported countries. | Add **single‑turn answer examples** that directly return the list after a brief clarification, and penalize extra turns in the loss function. |
| **cash_withdrawal_not_recognised** | `lost_or_stolen_card`, `compromised_card` | The model defaults to a security‑risk intent when a withdrawal is unknown. | Provide **balanced examples** where “not recognised” is a distinct intent from “lost/stolen”. |
| **balance_not_updated_after_bank_transfer** | `transfer_not_received_by_recipient`, `pending_transfer` | The model focuses on the *recipient* side rather than the *user’s balance* side. | Add **balance‑centric phrasing** to the training set (e.g., “my balance didn’t change”). |
| **top_up_by_bank_transfer_charge** | `transfer_into_account`, `fiat_currency_support` | The model treats fee queries as generic transfer questions. | Insert **fee‑specific utterances** for bank‑transfer top‑ups and map them to a distinct intent. |

**Overall Recommendation:**  
1. **Intent Hierarchy Review** – many drifts occur because the taxonomy treats a broad parent and its siblings as interchangeable. Introduce explicit *parent‑child* constraints.  
2. **Contrastive Training** – for each pair of frequently confused intents, add negative examples that highlight the lexical/semantic differences.  
3. **State‑Preserving Decoder** – keep the first‑turn intent locked unless a user explicitly changes the topic; otherwise, reuse the original label.  

---

## ⚠️ Persona Sensitivity Issues  

- **Current Test Set:** All failures involve the `HumanBase` persona. No non‑native speakers, age‑specific, or accessibility‑focused personas were exercised.  
- **Risk:** The model may behave differently (e.g., mis‑classify more often) for users with atypical phrasing, accents, or limited language proficiency.  

**Action Items**  
1. **Expand Persona Coverage** – generate synthetic dialogues for `NonNativeSpeaker`, `Elderly`, `VisuallyImpaired`, and `GenZ` personas.  
2. **Run Cross‑Persona Evaluation** – flag any intent that degrades > 20 % in recognition or efficiency when persona changes.  
3. **Add Persona‑Specific Slots** – e.g., ask for clarification in simpler language for non‑native speakers, avoid jargon for elderly users.  

---

## 🔄 UX & Efficiency Flaws  

| Issue | Affected Intents (examples) | Symptom | Suggested UX Improvement |
|-------|-----------------------------|---------|--------------------------|
| **Repeated Clarification After Information Already Provided** | `extra_charge_on_statement`, `disposable_card_limits`, `country_support`, `atm_support`, `cash_withdrawal_charge` | Bot asks for fee amount, description, or location multiple times. | Implement **slot‑completion checks**: before asking a question, verify the slot is already filled. |
| **Long Dialogues Without Resolution** | `extra_charge_on_statement` (5 turns), `disposable_card_limits` (5+ turns), `exchange_charge` (≥5 turns), `card_arrival` (multiple turns without tracking number) | User never receives the final answer (e.g., fee amount, tracking number). | Add a **“handoff” or “summary” step** after the last required slot is collected, delivering the answer or escalating to a human. |
| **Intent Switching Mid‑Conversation** | `card_payment_fee_charged`, `virtual_card_not_working`, `pending_transfer`, `top_up_by_card`, `order_physical_card` | Bot flips between related intents, causing confusion. | Enforce **intent stability**: once an intent is selected, keep it unless the user explicitly re‑states a different goal. |
| **Missing Final Action (e.g., no confirmation, no next‑step)** | `cancel_transfer`, `change_pin`, `order_physical_card`, `card_arrival`, `compromised_card` | Dialogue ends with open questions or “we’ll look into it” but no concrete next step. | Add a **“next‑step” template** that always confirms what will happen (e.g., “Your transfer has been cancelled – you’ll receive a confirmation email”). |
| **Over‑Specific Follow‑Ups for Simple Queries** | `atm_support` (asks method, fee‑free preference), `cash_withdrawal_charge` (asks if fee could be exchange‑related) | Extra turns that do not add value. | Use **confidence‑threshold gating**: if intent confidence > 0.9 and required slots are filled, answer immediately. |
| **Inconsistent Slot Naming / Missing Slots** | `verify_source_of_funds` (switches to `receiving_money`), `pending_cash_withdrawal` (switches to `cash_withdrawal_not_recognised`) | Slots from a different intent are collected, leading to wasted turns. | Tighten **slot‑intent binding** in the dialogue manager; reject slots that belong to another intent. |

---

### Quick Wins (high impact, low effort)

1. **Slot‑Filled Guardrails** – before each clarification, check if the slot already exists.  
2. **Intent Lock‑After‑First‑Turn** – keep the first predicted intent unless the user explicitly changes the request.  
3. **One‑Turn Answer Templates** for high‑frequency “information‑only” intents (`country_support`, `atm_support`, `cash_withdrawal_charge`).  
4. **Add Missing Intent Samples** (`order_physical_card`, `request_refund`, `change_pin`) to the training corpus.  
5. **Introduce Persona‑Diverse Test Sets** and run a regression suite to catch any hidden bias early.  

--- 

*Prepared by the QA Architecture team – Senior AI Tech Lead*