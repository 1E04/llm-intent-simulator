# Statistical Evaluation for run_003_openai-gpt-oss-120b

## Overall Metrics
- **Total Dialogues:** 770
- **Overall Accurate (Absolute):** 624
- **Overall Accuracy (Percentage):** 81.04%
- **Average Turns per Dialogue:** 2.04

## Prediction Stability
- **Right-to-Wrong Flips (Total across run):** 0
- **Wrong-to-Right Flips (Total across run):** 0

## Accuracy and Average Turns by Persona Style
| Persona | Total Dialogues | Accurate (Abs) | Accuracy (%) | Avg Turns |
|---------|-----------------|----------------|--------------|-----------|
| HumanBase | 770 | 624 | 81.04% | 2.04 |

## Best and Worst Predicted Labels
| Target Intent | Total | Accurate | Accuracy (%) |
|---------------|-------|----------|--------------|
| card_about_to_expire | 10 | 10 | 100.00% |
| verify_top_up | 10 | 10 | 100.00% |
| declined_cash_withdrawal | 10 | 10 | 100.00% |
| cancel_transfer | 10 | 10 | 100.00% |
| top_up_by_cash_or_cheque | 10 | 10 | 100.00% |
| top_up_limits | 10 | 10 | 100.00% |
| card_payment_not_recognised | 10 | 10 | 100.00% |
| terminate_account | 10 | 10 | 100.00% |
| get_pin | 10 | 10 | 100.00% |
| lost_or_stolen_card | 10 | 10 | 100.00% |
| contactless_not_working | 10 | 10 | 100.00% |
| transfer_fee_charged | 10 | 10 | 100.00% |
| declined_card_payment | 10 | 10 | 100.00% |
| get_disposable_virtual_card | 10 | 10 | 100.00% |
| atm_support | 10 | 10 | 100.00% |
| card_swallowed | 10 | 10 | 100.00% |
| compromised_card | 10 | 10 | 100.00% |
| card_payment_wrong_exchange_rate | 10 | 10 | 100.00% |
| transaction_charged_twice | 10 | 10 | 100.00% |
| pending_cash_withdrawal | 10 | 10 | 100.00% |
| supported_cards_and_currencies | 10 | 10 | 100.00% |
| transfer_timing | 10 | 10 | 100.00% |
| automatic_top_up | 10 | 10 | 100.00% |
| cash_withdrawal_charge | 10 | 10 | 100.00% |
| pending_card_payment | 10 | 10 | 100.00% |
| passcode_forgotten | 10 | 10 | 100.00% |
| change_pin | 10 | 10 | 100.00% |
| exchange_rate | 10 | 10 | 100.00% |
| age_limit | 10 | 10 | 100.00% |
| disposable_card_limits | 10 | 10 | 100.00% |
| balance_not_updated_after_cheque_or_cash_deposit | 10 | 10 | 100.00% |
| Refund_not_showing_up | 10 | 10 | 100.00% |
| edit_personal_details | 10 | 10 | 100.00% |
| lost_or_stolen_phone | 10 | 10 | 100.00% |
| top_up_failed | 10 | 9 | 90.00% |
| transfer_into_account | 10 | 9 | 90.00% |
| card_delivery_estimate | 10 | 9 | 90.00% |
| country_support | 10 | 9 | 90.00% |
| failed_transfer | 10 | 9 | 90.00% |
| activate_my_card | 10 | 9 | 90.00% |
| wrong_amount_of_cash_received | 10 | 9 | 90.00% |
| verify_my_identity | 10 | 9 | 90.00% |
| reverted_card_payment | 10 | 8 | 80.00% |
| pin_blocked | 10 | 8 | 80.00% |
| getting_virtual_card | 10 | 8 | 80.00% |
| request_refund | 10 | 8 | 80.00% |
| top_up_reverted | 10 | 8 | 80.00% |
| exchange_charge | 10 | 8 | 80.00% |
| visa_or_mastercard | 10 | 8 | 80.00% |
| getting_spare_card | 10 | 8 | 80.00% |
| pending_top_up | 10 | 8 | 80.00% |
| why_verify_identity | 10 | 7 | 70.00% |
| declined_transfer | 10 | 7 | 70.00% |
| balance_not_updated_after_bank_transfer | 10 | 7 | 70.00% |
| order_physical_card | 10 | 7 | 70.00% |
| top_up_by_card_charge | 10 | 7 | 70.00% |
| apple_pay_or_google_pay | 10 | 7 | 70.00% |
| beneficiary_not_allowed | 10 | 6 | 60.00% |
| pending_transfer | 10 | 6 | 60.00% |
| verify_source_of_funds | 10 | 6 | 60.00% |
| unable_to_verify_identity | 10 | 6 | 60.00% |
| direct_debit_payment_not_recognised | 10 | 6 | 60.00% |
| card_payment_fee_charged | 10 | 6 | 60.00% |
| cash_withdrawal_not_recognised | 10 | 6 | 60.00% |
| topping_up_by_card | 10 | 6 | 60.00% |
| card_linking | 10 | 6 | 60.00% |
| transfer_not_received_by_recipient | 10 | 5 | 50.00% |
| top_up_by_bank_transfer_charge | 10 | 5 | 50.00% |
| fiat_currency_support | 10 | 5 | 50.00% |
| wrong_exchange_rate_for_cash_withdrawal | 10 | 5 | 50.00% |
| virtual_card_not_working | 10 | 5 | 50.00% |
| card_not_working | 10 | 4 | 40.00% |
| exchange_via_app | 10 | 4 | 40.00% |
| card_arrival | 10 | 4 | 40.00% |
| receiving_money | 10 | 3 | 30.00% |
| extra_charge_on_statement | 10 | 3 | 30.00% |
| card_acceptance | 10 | 1 | 10.00% |

## Top Misclassifications (Target -> Predicted)
| Target Intent | Predicted Intent | Count |
|---------------|------------------|-------|
| card_arrival | card_delivery_estimate | 6 |
| card_not_working | declined_card_payment | 5 |
| exchange_via_app | exchange_rate | 4 |
| card_acceptance | country_support | 4 |
| top_up_by_bank_transfer_charge | transfer_fee_charged | 4 |
| unable_to_verify_identity | verify_my_identity | 4 |
| cash_withdrawal_not_recognised | lost_or_stolen_card | 4 |
| receiving_money | transfer_into_account | 4 |
| extra_charge_on_statement | card_payment_fee_charged | 4 |
| verify_source_of_funds | receiving_money | 3 |
| card_acceptance | visa_or_mastercard | 3 |
| transfer_not_received_by_recipient | transfer_timing | 3 |
| direct_debit_payment_not_recognised | card_payment_not_recognised | 3 |
| receiving_money | fiat_currency_support | 3 |
| topping_up_by_card | top_up_reverted | 3 |
| virtual_card_not_working | disposable_card_limits | 2 |
| card_payment_fee_charged | exchange_charge | 2 |
| top_up_reverted | top_up_failed | 2 |
| wrong_exchange_rate_for_cash_withdrawal | atm_support | 2 |
| card_linking | lost_or_stolen_card | 2 |
