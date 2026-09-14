# Statistical Evaluation for run_003_openai-gpt-oss-120b

## Overall Metrics
- **Total Dialogues:** 924
- **Overall Accurate (Absolute):** 539
- **Overall Accuracy (Percentage):** 58.33%
- **Average Turns per Dialogue:** 2.22

## Prediction Stability
- **Right-to-Wrong Flips (Total across run):** 0
- **Wrong-to-Right Flips (Total across run):** 0

## Accuracy and Average Turns by Persona Style
| Persona | Total Dialogues | Accurate (Abs) | Accuracy (%) | Avg Turns |
|---------|-----------------|----------------|--------------|-----------|
| Angry Layperson | 154 | 80 | 51.95% | 2.36 |
| Gen-Z Slang | 154 | 91 | 59.09% | 2.22 |
| Non-Native Speaker | 154 | 110 | 71.43% | 2.10 |
| Panicking Emergency | 154 | 76 | 49.35% | 2.28 |
| Polite Expert | 154 | 109 | 70.78% | 1.99 |
| Short Wording | 154 | 73 | 47.40% | 2.36 |

## Best and Worst Predicted Labels
| Target Intent | Total | Accurate | Accuracy (%) |
|---------------|-------|----------|--------------|
| lost_or_stolen_card | 12 | 12 | 100.00% |
| declined_cash_withdrawal | 12 | 12 | 100.00% |
| wrong_amount_of_cash_received | 12 | 12 | 100.00% |
| pending_card_payment | 12 | 12 | 100.00% |
| balance_not_updated_after_cheque_or_cash_deposit | 12 | 12 | 100.00% |
| Refund_not_showing_up | 12 | 12 | 100.00% |
| edit_personal_details | 12 | 12 | 100.00% |
| transfer_not_received_by_recipient | 12 | 12 | 100.00% |
| transaction_charged_twice | 12 | 12 | 100.00% |
| card_swallowed | 12 | 12 | 100.00% |
| cash_withdrawal_charge | 12 | 12 | 100.00% |
| card_linking | 12 | 12 | 100.00% |
| transfer_fee_charged | 12 | 12 | 100.00% |
| cancel_transfer | 12 | 12 | 100.00% |
| card_payment_wrong_exchange_rate | 12 | 12 | 100.00% |
| declined_card_payment | 12 | 12 | 100.00% |
| cash_withdrawal_not_recognised | 12 | 12 | 100.00% |
| balance_not_updated_after_bank_transfer | 12 | 11 | 91.67% |
| top_up_by_card_charge | 12 | 11 | 91.67% |
| top_up_failed | 12 | 11 | 91.67% |
| lost_or_stolen_phone | 12 | 11 | 91.67% |
| exchange_charge | 12 | 11 | 91.67% |
| passcode_forgotten | 12 | 11 | 91.67% |
| card_payment_not_recognised | 12 | 10 | 83.33% |
| unable_to_verify_identity | 12 | 10 | 83.33% |
| pending_cash_withdrawal | 12 | 10 | 83.33% |
| age_limit | 12 | 10 | 83.33% |
| order_physical_card | 12 | 9 | 75.00% |
| pending_transfer | 12 | 9 | 75.00% |
| get_disposable_virtual_card | 12 | 9 | 75.00% |
| card_payment_fee_charged | 12 | 9 | 75.00% |
| top_up_reverted | 12 | 9 | 75.00% |
| disposable_card_limits | 12 | 8 | 66.67% |
| direct_debit_payment_not_recognised | 12 | 8 | 66.67% |
| top_up_limits | 12 | 8 | 66.67% |
| wrong_exchange_rate_for_cash_withdrawal | 12 | 8 | 66.67% |
| fiat_currency_support | 12 | 8 | 66.67% |
| verify_source_of_funds | 12 | 8 | 66.67% |
| getting_virtual_card | 12 | 7 | 58.33% |
| failed_transfer | 12 | 7 | 58.33% |
| reverted_card_payment | 12 | 7 | 58.33% |
| compromised_card | 12 | 7 | 58.33% |
| contactless_not_working | 12 | 7 | 58.33% |
| terminate_account | 12 | 7 | 58.33% |
| card_delivery_estimate | 12 | 7 | 58.33% |
| beneficiary_not_allowed | 12 | 6 | 50.00% |
| declined_transfer | 12 | 6 | 50.00% |
| pending_top_up | 12 | 6 | 50.00% |
| card_about_to_expire | 12 | 6 | 50.00% |
| verify_my_identity | 12 | 6 | 50.00% |
| extra_charge_on_statement | 12 | 5 | 41.67% |
| top_up_by_bank_transfer_charge | 12 | 5 | 41.67% |
| card_arrival | 12 | 5 | 41.67% |
| get_pin | 12 | 5 | 41.67% |
| top_up_by_cash_or_cheque | 12 | 5 | 41.67% |
| automatic_top_up | 12 | 4 | 33.33% |
| pin_blocked | 12 | 4 | 33.33% |
| country_support | 12 | 4 | 33.33% |
| exchange_via_app | 12 | 4 | 33.33% |
| why_verify_identity | 12 | 4 | 33.33% |
| transfer_timing | 12 | 3 | 25.00% |
| activate_my_card | 12 | 3 | 25.00% |
| getting_spare_card | 12 | 3 | 25.00% |
| visa_or_mastercard | 12 | 1 | 8.33% |
| topping_up_by_card | 12 | 1 | 8.33% |
| supported_cards_and_currencies | 12 | 1 | 8.33% |
| card_not_working | 12 | 0 | 0.00% |
| transfer_into_account | 12 | 0 | 0.00% |
| exchange_rate | 12 | 0 | 0.00% |
| apple_pay_or_google_pay | 12 | 0 | 0.00% |
| receiving_money | 12 | 0 | 0.00% |
| atm_support | 12 | 0 | 0.00% |
| virtual_card_not_working | 12 | 0 | 0.00% |
| request_refund | 12 | 0 | 0.00% |
| change_pin | 12 | 0 | 0.00% |
| verify_top_up | 12 | 0 | 0.00% |
| card_acceptance | 12 | 0 | 0.00% |

## Top Misclassifications (Target -> Predicted)
| Target Intent | Predicted Intent | Count |
|---------------|------------------|-------|
| virtual_card_not_working | declined_card_payment | 12 |
| visa_or_mastercard | declined_card_payment | 11 |
| card_not_working | declined_card_payment | 11 |
| exchange_rate | card_payment_wrong_exchange_rate | 10 |
| apple_pay_or_google_pay | declined_card_payment | 10 |
| supported_cards_and_currencies | declined_card_payment | 9 |
| card_acceptance | declined_card_payment | 9 |
| transfer_into_account | balance_not_updated_after_bank_transfer | 8 |
| top_up_by_bank_transfer_charge | transfer_fee_charged | 7 |
| card_arrival | card_delivery_estimate | 7 |
| topping_up_by_card | top_up_failed | 7 |
| change_pin | pin_blocked | 7 |
| beneficiary_not_allowed | declined_transfer | 6 |
| activate_my_card | declined_card_payment | 6 |
| verify_top_up | pending_top_up | 6 |
| atm_support | declined_cash_withdrawal | 6 |
| declined_transfer | failed_transfer | 6 |
| extra_charge_on_statement | card_payment_fee_charged | 5 |
| receiving_money | balance_not_updated_after_bank_transfer | 5 |
| card_about_to_expire | declined_card_payment | 5 |
