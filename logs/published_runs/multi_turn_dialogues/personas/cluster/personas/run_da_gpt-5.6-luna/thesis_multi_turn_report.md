# Multi-Turn Intent Recognition Evaluation Report

**Target Model:** gpt-5.4-nano | **Simulator Model:** gpt-oss-120b | **Total Dialogues:** 2310

## Overall Performance Metrics
| Metric | Value |
|---|---|
| Dialogue Success Rate (Context Maintained) | 71.56% |
| Premature Classification Rate (Out of Cluster) | 9.65% |
| Inconclusive Dialogues (Max Turns Reached) | 14.29% |
| Average Turns to Resolution | 2.06 |

## Persona Impact Analysis (Linguistic Variance)
This table demonstrates the system's robustness across different user communication styles.

| Persona | Total | Success Rate | Premature Fail Rate | Avg Turns to Resolution |
|---|---|---|---|---|
| Angry Layperson | 385 | 69.4% | 10.9% | 2.07 |
| Gen-Z Slang | 385 | 71.2% | 9.6% | 2.03 |
| Non-Native Speaker | 385 | 77.7% | 6.0% | 2.02 |
| Panicking Emergency | 385 | 65.7% | 11.4% | 2.07 |
| Polite Expert | 385 | 76.6% | 8.1% | 2.00 |
| Short Wording | 385 | 68.8% | 11.9% | 2.18 |

## Detailed Persona Breakdowns
Performance of specific intents for each persona.

### Angry Layperson
**Intents with 0% Success Rate:** 5

| Intent | Total | Success Rate |
|---|---|---|
| top_up_limits | 5 | 100.0% |
| verify_my_identity | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| balance_not_updated_after_bank_transfer | 5 | 100.0% |
| top_up_reverted | 5 | 100.0% |
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| lost_or_stolen_card | 5 | 100.0% |
| transfer_not_received_by_recipient | 5 | 100.0% |
| edit_personal_details | 5 | 100.0% |
| declined_transfer | 5 | 100.0% |
| pending_card_payment | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| top_up_failed | 5 | 100.0% |
| exchange_charge | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| activate_my_card | 5 | 100.0% |
| Refund_not_showing_up | 5 | 100.0% |
| cash_withdrawal_not_recognised | 5 | 100.0% |
| declined_card_payment | 5 | 100.0% |
| transaction_charged_twice | 5 | 100.0% |
| pending_transfer | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| card_payment_not_recognised | 5 | 100.0% |
| lost_or_stolen_phone | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| cash_withdrawal_charge | 5 | 100.0% |
| why_verify_identity | 5 | 100.0% |
| card_about_to_expire | 5 | 100.0% |
| pending_top_up | 5 | 100.0% |
| terminate_account | 5 | 80.0% |
| order_physical_card | 5 | 80.0% |
| cancel_transfer | 5 | 80.0% |
| top_up_by_card_charge | 5 | 80.0% |
| top_up_by_bank_transfer_charge | 5 | 80.0% |
| failed_transfer | 5 | 80.0% |
| compromised_card | 5 | 80.0% |
| beneficiary_not_allowed | 5 | 80.0% |
| direct_debit_payment_not_recognised | 5 | 80.0% |
| verify_source_of_funds | 5 | 80.0% |
| automatic_top_up | 5 | 80.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 80.0% |
| change_pin | 5 | 80.0% |
| getting_spare_card | 5 | 80.0% |
| card_payment_fee_charged | 5 | 80.0% |
| get_pin | 5 | 80.0% |
| card_delivery_estimate | 5 | 60.0% |
| exchange_rate | 5 | 60.0% |
| visa_or_mastercard | 5 | 60.0% |
| contactless_not_working | 5 | 60.0% |
| verify_top_up | 5 | 60.0% |
| age_limit | 5 | 60.0% |
| reverted_card_payment | 5 | 60.0% |
| passcode_forgotten | 5 | 60.0% |
| disposable_card_limits | 5 | 60.0% |
| fiat_currency_support | 5 | 40.0% |
| request_refund | 5 | 40.0% |
| country_support | 5 | 40.0% |
| get_disposable_virtual_card | 5 | 40.0% |
| card_linking | 5 | 40.0% |
| supported_cards_and_currencies | 5 | 40.0% |
| unable_to_verify_identity | 5 | 40.0% |
| transfer_timing | 5 | 40.0% |
| pin_blocked | 5 | 40.0% |
| apple_pay_or_google_pay | 5 | 20.0% |
| extra_charge_on_statement | 5 | 20.0% |
| receiving_money | 5 | 20.0% |
| top_up_by_cash_or_cheque | 5 | 20.0% |
| card_not_working | 5 | 20.0% |
| topping_up_by_card | 5 | 20.0% |
| getting_virtual_card | 5 | 20.0% |
| card_arrival | 5 | 20.0% |
| virtual_card_not_working | 5 | 0.0% |
| card_acceptance | 5 | 0.0% |
| atm_support | 5 | 0.0% |
| transfer_into_account | 5 | 0.0% |
| exchange_via_app | 5 | 0.0% |

### Gen-Z Slang
**Intents with 0% Success Rate:** 7

| Intent | Total | Success Rate |
|---|---|---|
| balance_not_updated_after_bank_transfer | 5 | 100.0% |
| cancel_transfer | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| disposable_card_limits | 5 | 100.0% |
| edit_personal_details | 5 | 100.0% |
| transaction_charged_twice | 5 | 100.0% |
| order_physical_card | 5 | 100.0% |
| pin_blocked | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| fiat_currency_support | 5 | 100.0% |
| top_up_failed | 5 | 100.0% |
| beneficiary_not_allowed | 5 | 100.0% |
| lost_or_stolen_phone | 5 | 100.0% |
| cash_withdrawal_not_recognised | 5 | 100.0% |
| card_delivery_estimate | 5 | 100.0% |
| age_limit | 5 | 100.0% |
| lost_or_stolen_card | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| passcode_forgotten | 5 | 100.0% |
| card_about_to_expire | 5 | 100.0% |
| card_linking | 5 | 100.0% |
| terminate_account | 5 | 100.0% |
| get_pin | 5 | 100.0% |
| exchange_charge | 5 | 100.0% |
| top_up_limits | 5 | 100.0% |
| verify_top_up | 5 | 100.0% |
| declined_card_payment | 5 | 100.0% |
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| getting_spare_card | 5 | 100.0% |
| cash_withdrawal_charge | 5 | 100.0% |
| Refund_not_showing_up | 5 | 80.0% |
| top_up_by_bank_transfer_charge | 5 | 80.0% |
| verify_my_identity | 5 | 80.0% |
| pending_card_payment | 5 | 80.0% |
| declined_transfer | 5 | 80.0% |
| visa_or_mastercard | 5 | 80.0% |
| automatic_top_up | 5 | 80.0% |
| top_up_reverted | 5 | 80.0% |
| supported_cards_and_currencies | 5 | 80.0% |
| activate_my_card | 5 | 80.0% |
| pending_transfer | 5 | 80.0% |
| top_up_by_card_charge | 5 | 80.0% |
| get_disposable_virtual_card | 5 | 80.0% |
| transfer_timing | 5 | 60.0% |
| change_pin | 5 | 60.0% |
| request_refund | 5 | 60.0% |
| direct_debit_payment_not_recognised | 5 | 60.0% |
| country_support | 5 | 60.0% |
| reverted_card_payment | 5 | 60.0% |
| why_verify_identity | 5 | 60.0% |
| compromised_card | 5 | 60.0% |
| pending_top_up | 5 | 60.0% |
| transfer_not_received_by_recipient | 5 | 60.0% |
| card_payment_not_recognised | 5 | 60.0% |
| exchange_rate | 5 | 60.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 60.0% |
| top_up_by_cash_or_cheque | 5 | 40.0% |
| card_acceptance | 5 | 40.0% |
| getting_virtual_card | 5 | 40.0% |
| card_payment_fee_charged | 5 | 40.0% |
| transfer_into_account | 5 | 40.0% |
| exchange_via_app | 5 | 40.0% |
| card_arrival | 5 | 40.0% |
| failed_transfer | 5 | 20.0% |
| topping_up_by_card | 5 | 20.0% |
| unable_to_verify_identity | 5 | 20.0% |
| card_not_working | 5 | 20.0% |
| verify_source_of_funds | 5 | 0.0% |
| receiving_money | 5 | 0.0% |
| atm_support | 5 | 0.0% |
| apple_pay_or_google_pay | 5 | 0.0% |
| virtual_card_not_working | 5 | 0.0% |
| contactless_not_working | 5 | 0.0% |
| extra_charge_on_statement | 5 | 0.0% |

### Non-Native Speaker
**Intents with 0% Success Rate:** 3

| Intent | Total | Success Rate |
|---|---|---|
| transfer_into_account | 5 | 100.0% |
| top_up_failed | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| pending_top_up | 5 | 100.0% |
| beneficiary_not_allowed | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| card_delivery_estimate | 5 | 100.0% |
| balance_not_updated_after_bank_transfer | 5 | 100.0% |
| pending_card_payment | 5 | 100.0% |
| declined_transfer | 5 | 100.0% |
| top_up_limits | 5 | 100.0% |
| change_pin | 5 | 100.0% |
| cash_withdrawal_charge | 5 | 100.0% |
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| get_disposable_virtual_card | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| exchange_charge | 5 | 100.0% |
| disposable_card_limits | 5 | 100.0% |
| failed_transfer | 5 | 100.0% |
| terminate_account | 5 | 100.0% |
| lost_or_stolen_card | 5 | 100.0% |
| passcode_forgotten | 5 | 100.0% |
| pending_transfer | 5 | 100.0% |
| cash_withdrawal_not_recognised | 5 | 100.0% |
| get_pin | 5 | 100.0% |
| verify_top_up | 5 | 100.0% |
| age_limit | 5 | 100.0% |
| top_up_by_cash_or_cheque | 5 | 100.0% |
| declined_card_payment | 5 | 100.0% |
| Refund_not_showing_up | 5 | 100.0% |
| request_refund | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| edit_personal_details | 5 | 100.0% |
| transaction_charged_twice | 5 | 100.0% |
| getting_spare_card | 5 | 100.0% |
| card_about_to_expire | 5 | 100.0% |
| verify_my_identity | 5 | 100.0% |
| supported_cards_and_currencies | 5 | 100.0% |
| top_up_reverted | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| activate_my_card | 5 | 80.0% |
| exchange_rate | 5 | 80.0% |
| transfer_not_received_by_recipient | 5 | 80.0% |
| reverted_card_payment | 5 | 80.0% |
| order_physical_card | 5 | 80.0% |
| fiat_currency_support | 5 | 80.0% |
| cancel_transfer | 5 | 80.0% |
| automatic_top_up | 5 | 80.0% |
| lost_or_stolen_phone | 5 | 80.0% |
| country_support | 5 | 80.0% |
| card_payment_not_recognised | 5 | 80.0% |
| compromised_card | 5 | 80.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 80.0% |
| top_up_by_card_charge | 5 | 80.0% |
| card_not_working | 5 | 60.0% |
| contactless_not_working | 5 | 60.0% |
| pin_blocked | 5 | 60.0% |
| card_linking | 5 | 60.0% |
| direct_debit_payment_not_recognised | 5 | 60.0% |
| visa_or_mastercard | 5 | 60.0% |
| transfer_timing | 5 | 60.0% |
| getting_virtual_card | 5 | 60.0% |
| topping_up_by_card | 5 | 40.0% |
| card_acceptance | 5 | 40.0% |
| receiving_money | 5 | 40.0% |
| unable_to_verify_identity | 5 | 20.0% |
| card_payment_fee_charged | 5 | 20.0% |
| extra_charge_on_statement | 5 | 20.0% |
| atm_support | 5 | 20.0% |
| exchange_via_app | 5 | 20.0% |
| apple_pay_or_google_pay | 5 | 20.0% |
| why_verify_identity | 5 | 20.0% |
| virtual_card_not_working | 5 | 20.0% |
| card_arrival | 5 | 0.0% |
| verify_source_of_funds | 5 | 0.0% |
| top_up_by_bank_transfer_charge | 5 | 0.0% |

### Panicking Emergency
**Intents with 0% Success Rate:** 7

| Intent | Total | Success Rate |
|---|---|---|
| transaction_charged_twice | 5 | 100.0% |
| lost_or_stolen_phone | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| balance_not_updated_after_bank_transfer | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| pending_card_payment | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| cash_withdrawal_charge | 5 | 100.0% |
| Refund_not_showing_up | 5 | 100.0% |
| disposable_card_limits | 5 | 100.0% |
| card_about_to_expire | 5 | 100.0% |
| card_payment_not_recognised | 5 | 100.0% |
| age_limit | 5 | 100.0% |
| exchange_charge | 5 | 100.0% |
| transfer_not_received_by_recipient | 5 | 100.0% |
| top_up_limits | 5 | 100.0% |
| lost_or_stolen_card | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| exchange_rate | 5 | 100.0% |
| top_up_by_card_charge | 5 | 100.0% |
| pending_top_up | 5 | 100.0% |
| declined_card_payment | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| cancel_transfer | 5 | 100.0% |
| cash_withdrawal_not_recognised | 5 | 100.0% |
| visa_or_mastercard | 5 | 80.0% |
| automatic_top_up | 5 | 80.0% |
| passcode_forgotten | 5 | 80.0% |
| reverted_card_payment | 5 | 80.0% |
| card_delivery_estimate | 5 | 80.0% |
| verify_source_of_funds | 5 | 80.0% |
| failed_transfer | 5 | 80.0% |
| pin_blocked | 5 | 80.0% |
| edit_personal_details | 5 | 80.0% |
| top_up_reverted | 5 | 80.0% |
| card_payment_fee_charged | 5 | 80.0% |
| terminate_account | 5 | 80.0% |
| transfer_into_account | 5 | 80.0% |
| verify_top_up | 5 | 60.0% |
| activate_my_card | 5 | 60.0% |
| declined_transfer | 5 | 60.0% |
| direct_debit_payment_not_recognised | 5 | 60.0% |
| top_up_by_cash_or_cheque | 5 | 60.0% |
| why_verify_identity | 5 | 60.0% |
| get_pin | 5 | 60.0% |
| contactless_not_working | 5 | 60.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 60.0% |
| pending_transfer | 5 | 60.0% |
| compromised_card | 5 | 60.0% |
| order_physical_card | 5 | 40.0% |
| beneficiary_not_allowed | 5 | 40.0% |
| change_pin | 5 | 40.0% |
| get_disposable_virtual_card | 5 | 40.0% |
| top_up_failed | 5 | 40.0% |
| getting_virtual_card | 5 | 40.0% |
| exchange_via_app | 5 | 40.0% |
| supported_cards_and_currencies | 5 | 40.0% |
| card_arrival | 5 | 40.0% |
| verify_my_identity | 5 | 40.0% |
| getting_spare_card | 5 | 40.0% |
| unable_to_verify_identity | 5 | 40.0% |
| transfer_timing | 5 | 40.0% |
| request_refund | 5 | 40.0% |
| card_not_working | 5 | 20.0% |
| card_acceptance | 5 | 20.0% |
| topping_up_by_card | 5 | 20.0% |
| card_linking | 5 | 20.0% |
| extra_charge_on_statement | 5 | 20.0% |
| top_up_by_bank_transfer_charge | 5 | 0.0% |
| apple_pay_or_google_pay | 5 | 0.0% |
| virtual_card_not_working | 5 | 0.0% |
| fiat_currency_support | 5 | 0.0% |
| receiving_money | 5 | 0.0% |
| country_support | 5 | 0.0% |
| atm_support | 5 | 0.0% |

### Polite Expert
**Intents with 0% Success Rate:** 5

| Intent | Total | Success Rate |
|---|---|---|
| beneficiary_not_allowed | 5 | 100.0% |
| terminate_account | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| failed_transfer | 5 | 100.0% |
| balance_not_updated_after_bank_transfer | 5 | 100.0% |
| lost_or_stolen_phone | 5 | 100.0% |
| card_payment_not_recognised | 5 | 100.0% |
| lost_or_stolen_card | 5 | 100.0% |
| visa_or_mastercard | 5 | 100.0% |
| top_up_by_cash_or_cheque | 5 | 100.0% |
| order_physical_card | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| edit_personal_details | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| exchange_rate | 5 | 100.0% |
| declined_transfer | 5 | 100.0% |
| Refund_not_showing_up | 5 | 100.0% |
| top_up_limits | 5 | 100.0% |
| direct_debit_payment_not_recognised | 5 | 100.0% |
| card_delivery_estimate | 5 | 100.0% |
| top_up_failed | 5 | 100.0% |
| cash_withdrawal_not_recognised | 5 | 100.0% |
| card_about_to_expire | 5 | 100.0% |
| get_pin | 5 | 100.0% |
| verify_my_identity | 5 | 100.0% |
| pending_card_payment | 5 | 100.0% |
| change_pin | 5 | 100.0% |
| getting_spare_card | 5 | 100.0% |
| pin_blocked | 5 | 100.0% |
| top_up_reverted | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| request_refund | 5 | 100.0% |
| verify_top_up | 5 | 80.0% |
| pending_transfer | 5 | 80.0% |
| passcode_forgotten | 5 | 80.0% |
| age_limit | 5 | 80.0% |
| supported_cards_and_currencies | 5 | 80.0% |
| disposable_card_limits | 5 | 80.0% |
| transaction_charged_twice | 5 | 80.0% |
| reverted_card_payment | 5 | 80.0% |
| activate_my_card | 5 | 80.0% |
| why_verify_identity | 5 | 80.0% |
| fiat_currency_support | 5 | 80.0% |
| top_up_by_card_charge | 5 | 80.0% |
| compromised_card | 5 | 80.0% |
| get_disposable_virtual_card | 5 | 80.0% |
| country_support | 5 | 80.0% |
| cash_withdrawal_charge | 5 | 80.0% |
| transfer_timing | 5 | 80.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 80.0% |
| declined_card_payment | 5 | 80.0% |
| automatic_top_up | 5 | 80.0% |
| pending_top_up | 5 | 60.0% |
| card_linking | 5 | 60.0% |
| transfer_into_account | 5 | 60.0% |
| topping_up_by_card | 5 | 60.0% |
| card_payment_fee_charged | 5 | 60.0% |
| extra_charge_on_statement | 5 | 60.0% |
| transfer_not_received_by_recipient | 5 | 60.0% |
| getting_virtual_card | 5 | 60.0% |
| exchange_charge | 5 | 60.0% |
| cancel_transfer | 5 | 60.0% |
| top_up_by_bank_transfer_charge | 5 | 40.0% |
| card_acceptance | 5 | 40.0% |
| exchange_via_app | 5 | 40.0% |
| card_not_working | 5 | 20.0% |
| receiving_money | 5 | 20.0% |
| contactless_not_working | 5 | 20.0% |
| card_arrival | 5 | 20.0% |
| virtual_card_not_working | 5 | 0.0% |
| apple_pay_or_google_pay | 5 | 0.0% |
| verify_source_of_funds | 5 | 0.0% |
| atm_support | 5 | 0.0% |
| unable_to_verify_identity | 5 | 0.0% |

### Short Wording
**Intents with 0% Success Rate:** 4

| Intent | Total | Success Rate |
|---|---|---|
| balance_not_updated_after_cheque_or_cash_deposit | 5 | 100.0% |
| get_pin | 5 | 100.0% |
| order_physical_card | 5 | 100.0% |
| edit_personal_details | 5 | 100.0% |
| transaction_charged_twice | 5 | 100.0% |
| transfer_fee_charged | 5 | 100.0% |
| declined_card_payment | 5 | 100.0% |
| pending_transfer | 5 | 100.0% |
| disposable_card_limits | 5 | 100.0% |
| reverted_card_payment | 5 | 100.0% |
| top_up_limits | 5 | 100.0% |
| cash_withdrawal_charge | 5 | 100.0% |
| exchange_rate | 5 | 100.0% |
| automatic_top_up | 5 | 100.0% |
| card_swallowed | 5 | 100.0% |
| declined_cash_withdrawal | 5 | 100.0% |
| why_verify_identity | 5 | 100.0% |
| wrong_amount_of_cash_received | 5 | 100.0% |
| verify_my_identity | 5 | 100.0% |
| pending_cash_withdrawal | 5 | 100.0% |
| failed_transfer | 5 | 100.0% |
| pending_card_payment | 5 | 100.0% |
| top_up_by_card_charge | 5 | 100.0% |
| getting_spare_card | 5 | 100.0% |
| card_payment_wrong_exchange_rate | 5 | 100.0% |
| country_support | 5 | 80.0% |
| fiat_currency_support | 5 | 80.0% |
| card_linking | 5 | 80.0% |
| get_disposable_virtual_card | 5 | 80.0% |
| card_delivery_estimate | 5 | 80.0% |
| pending_top_up | 5 | 80.0% |
| request_refund | 5 | 80.0% |
| visa_or_mastercard | 5 | 80.0% |
| cancel_transfer | 5 | 80.0% |
| verify_top_up | 5 | 80.0% |
| card_payment_fee_charged | 5 | 80.0% |
| terminate_account | 5 | 80.0% |
| cash_withdrawal_not_recognised | 5 | 80.0% |
| declined_transfer | 5 | 80.0% |
| exchange_charge | 5 | 80.0% |
| lost_or_stolen_card | 5 | 80.0% |
| card_not_working | 5 | 80.0% |
| change_pin | 5 | 80.0% |
| transfer_timing | 5 | 80.0% |
| supported_cards_and_currencies | 5 | 80.0% |
| card_about_to_expire | 5 | 80.0% |
| passcode_forgotten | 5 | 60.0% |
| Refund_not_showing_up | 5 | 60.0% |
| balance_not_updated_after_bank_transfer | 5 | 60.0% |
| getting_virtual_card | 5 | 60.0% |
| transfer_not_received_by_recipient | 5 | 60.0% |
| wrong_exchange_rate_for_cash_withdrawal | 5 | 60.0% |
| unable_to_verify_identity | 5 | 60.0% |
| verify_source_of_funds | 5 | 60.0% |
| top_up_reverted | 5 | 60.0% |
| direct_debit_payment_not_recognised | 5 | 60.0% |
| card_payment_not_recognised | 5 | 60.0% |
| compromised_card | 5 | 40.0% |
| lost_or_stolen_phone | 5 | 40.0% |
| top_up_by_bank_transfer_charge | 5 | 40.0% |
| pin_blocked | 5 | 40.0% |
| contactless_not_working | 5 | 40.0% |
| card_arrival | 5 | 40.0% |
| exchange_via_app | 5 | 40.0% |
| extra_charge_on_statement | 5 | 20.0% |
| beneficiary_not_allowed | 5 | 20.0% |
| activate_my_card | 5 | 20.0% |
| atm_support | 5 | 20.0% |
| top_up_by_cash_or_cheque | 5 | 20.0% |
| topping_up_by_card | 5 | 20.0% |
| transfer_into_account | 5 | 20.0% |
| top_up_failed | 5 | 20.0% |
| age_limit | 5 | 20.0% |
| card_acceptance | 5 | 0.0% |
| virtual_card_not_working | 5 | 0.0% |
| receiving_money | 5 | 0.0% |
| apple_pay_or_google_pay | 5 | 0.0% |

