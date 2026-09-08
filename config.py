"""Configuration-driven onboarding journeys.

The country/customer-type matrix is deliberately data-driven so adding a new
market or customer type does not require rewriting the Flask routes.
"""


def field(name, label, type_="text", required=True, **kwargs):
    item = {"name": name, "label": label, "type": type_, "required": required}
    item.update(kwargs)
    return item


PRIVATE_COMMON_EMPLOYMENT = field(
    "employment_status", "Employment status", "select",
    options=["employed", "self_employed", "student", "unemployed", "retired"],
)

FLOWS = {
    "SE": {
        "private": {
            "title": "Sweden — Private individual",
            "steps": [
                {"title": "Identity & BankID-style verification", "description": "Collect the personal identity number and run a deterministic BankID-style identity mock.", "fields": [field("personal_number", "Personal identity number", placeholder="YYYYMMDD-NNNN"), field("identity_scenario", "Demo identity scenario", "select", options=["success", "manual_review", "fail", "expired"])], "integration": "identity"},
                {"title": "Contact details & address", "description": "Confirm contact details and validate the residential address with a mock lookup.", "fields": [field("email", "Email", "email"), field("phone", "Phone"), field("address", "Address"), field("postal_code", "Postal code"), field("city", "City"), field("address_scenario", "Demo address scenario", "select", options=["verified", "manual_review", "fail"])], "integration": "address"},
                {"title": "Consent, PEP/sanctions & tax residency", "description": "Capture consent, PEP declaration and tax residency.", "fields": [field("consent", "I consent to the processing required for this application", "checkbox"), field("pep_declared", "Are you a PEP or closely associated with a PEP?", "select", options=["no", "yes"]), field("tax_residency", "Tax residency")], "integration": "sanctions"},
                {"title": "Employment, income & household affordability", "description": "Collect employment, income, household costs, debt and dependants used by affordability rules.", "fields": [PRIVATE_COMMON_EMPLOYMENT, field("monthly_income", "Monthly income (SEK)", "number"), field("monthly_expenses", "Monthly household expenses (SEK)", "number"), field("monthly_debt_payments", "Monthly debt payments (SEK)", "number"), field("dependants", "Dependants", "number")], "integration": None},
                {"title": "Credit bureau & affordability decision", "description": "Run the deterministic credit-bureau and affordability mock using the financial information already collected.", "fields": [field("credit_scenario", "Demo credit scenario", "select", options=["good", "manual_review", "fail"])], "integration": "credit"},
                {"title": "Review summary, accept terms & submit", "description": "Review the application summary, accept the terms and submit.", "fields": [field("terms", "I confirm that the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
        "business": {
            "title": "Sweden — Business",
            "steps": [
                {"title": "Company details", "description": "Collect organisation number, legal name and legal form.", "fields": [field("org_number", "Organisation number"), field("legal_name", "Legal name"), field("legal_form", "Legal form", "select", options=["AB", "HB", "KB", "sole_trader"])], "integration": "registry"},
                {"title": "Representative & signatory rights", "description": "Confirm the authorised representative and authority to sign.", "fields": [field("representative_name", "Authorised representative"), field("representative_id", "Representative identity"), field("authority", "Signatory authority", "select", options=["authorised", "unknown"])], "integration": "representative"},
                {"title": "Beneficial owners & KYC", "description": "Collect beneficial owner information and run BankID-style UBO KYC plus sanctions screening.", "fields": [field("ubo_name", "Beneficial owner name"), field("ubo_ownership", "UBO ownership (%)", "number"), field("pep_declared", "Is the UBO a PEP or closely associated with a PEP?", "select", options=["no", "yes"])], "integration": "ubo_kyc_sanctions"},
                {"title": "Business activity & expected usage", "description": "Capture business activity, turnover, account purpose and expected usage.", "fields": [field("activity", "Business activity"), field("annual_turnover", "Annual turnover (SEK)", "number"), field("purpose", "Account purpose"), field("expected_usage", "Expected account usage")], "integration": "business_profile"},
                {"title": "KYB, sanctions/PEP & business credit", "description": "Run deterministic business risk and credit decisioning.", "fields": [field("business_risk", "Demo business risk", "select", options=["good", "manual_review", "fail"])], "integration": "business_credit"},
                {"title": "Review & sign", "description": "Review the business application, accept the terms and sign/submit.", "fields": [field("terms", "I confirm the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
    },
    "ES": {
        "private": {
            "title": "Spain — Private individual",
            "steps": [
                {"title": "DNI/NIE & Clave/DNIe verification", "description": "Collect DNI/NIE and run a deterministic document/Clave/DNIe-style identity mock.", "fields": [field("dni_nie", "DNI/NIE"), field("identity_method", "Verification method", "select", options=["Clave", "DNIe", "document_check"]), field("identity_scenario", "Demo identity scenario", "select", options=["success", "manual_review", "fail", "expired"])], "integration": "identity"},
                {"title": "Contact, province, address & tax residency", "description": "Confirm contact details, province, address and tax residency with address/province validation.", "fields": [field("email", "Email", "email"), field("phone", "Phone"), field("province", "Province"), field("address", "Address"), field("postal_code", "Postal code"), field("tax_residency", "Tax residency"), field("address_scenario", "Demo address scenario", "select", options=["verified", "manual_review", "fail"])], "integration": "address"},
                {"title": "Consent & PEP/sanctions", "description": "Capture consent and the PEP/sanctions declaration.", "fields": [field("consent", "I consent to the required processing", "checkbox"), field("pep_declared", "Are you a PEP or closely associated with a PEP?", "select", options=["no", "yes"])], "integration": "sanctions"},
                {"title": "Employment, income, housing & dependants", "description": "Collect financial inputs used by affordability rules.", "fields": [PRIVATE_COMMON_EMPLOYMENT, field("monthly_income", "Monthly income (EUR)", "number"), field("housing_cost", "Monthly housing cost (EUR)", "number"), field("monthly_debt_payments", "Monthly debt payments (EUR)", "number"), field("dependants", "Dependants", "number")], "integration": None},
                {"title": "Credit bureau & affordability decision", "description": "Run the credit-bureau and affordability mock.", "fields": [field("credit_scenario", "Demo credit scenario", "select", options=["good", "manual_review", "fail"])], "integration": "credit"},
                {"title": "Review summary, accept terms & submit", "description": "Review the application, accept the terms and submit.", "fields": [field("terms", "I confirm that the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
        "business": {
            "title": "Spain — Business",
            "steps": [
                {"title": "Company details", "description": "Collect company NIF, legal form and registered address.", "fields": [field("nif", "Company NIF"), field("legal_form", "Legal form", "select", options=["SL", "SA", "sole_trader"]), field("address", "Registered address")], "integration": "registry"},
                {"title": "Legal representative", "description": "Verify the legal representative using a DNI/NIE identity mock and authority check.", "fields": [field("representative_name", "Legal representative"), field("representative_id", "Representative DNI/NIE"), field("authority", "Authority", "select", options=["authorised", "unknown"])], "integration": "representative"},
                {"title": "Beneficial owners", "description": "Collect UBO ownership percentages and run KYC/sanctions screening.", "fields": [field("ubo_name", "UBO name"), field("ubo_ownership", "Ownership (%)", "number"), field("pep_declared", "Is the UBO a PEP or closely associated with a PEP?", "select", options=["no", "yes"])], "integration": "ubo_kyc_sanctions"},
                {"title": "Sector, turnover, VAT/tax & usage", "description": "Capture sector, turnover, VAT/tax details and expected account usage.", "fields": [field("sector", "Sector"), field("annual_turnover", "Annual turnover (EUR)", "number"), field("vat_status", "VAT/tax status", "select", options=["valid", "manual", "invalid"]), field("purpose", "Account purpose"), field("expected_usage", "Expected usage")], "integration": "business_profile"},
                {"title": "KYB, sanctions/PEP, business credit & IBAN", "description": "Run business credit/risk and verify the bank account.", "fields": [field("business_risk", "Demo business risk", "select", options=["good", "manual_review", "fail"]), field("iban", "IBAN"), field("account_name", "Account holder name"), field("bank_scenario", "Demo bank scenario", "select", options=["verified", "name_mismatch", "unreachable"])], "integration": "business_final"},
                {"title": "Review & sign", "description": "Review the business application, accept terms and sign/submit.", "fields": [field("terms", "I confirm the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
    },
    "PL": {
        "private": {
            "title": "Poland — Private individual",
            "steps": [
                {"title": "PESEL & eID-style verification", "description": "Collect PESEL and run an eID/Trusted Profile/mObywatel-style identity mock.", "fields": [field("pesel", "PESEL"), field("identity_method", "Verification method", "select", options=["eID", "Trusted Profile", "mObywatel"]), field("identity_scenario", "Demo identity scenario", "select", options=["success", "manual_review", "fail", "expired"])], "integration": "identity"},
                {"title": "Contact details & registered address", "description": "Confirm contact details and validate the registered address.", "fields": [field("email", "Email", "email"), field("phone", "Phone"), field("address", "Registered address"), field("postal_code", "Postal code"), field("city", "City"), field("address_scenario", "Demo address scenario", "select", options=["verified", "manual_review", "fail"])], "integration": "address"},
                {"title": "Consent & PEP/sanctions", "description": "Capture consent and PEP/sanctions declaration.", "fields": [field("consent", "I consent to the required processing", "checkbox"), field("pep_declared", "Are you a PEP or closely associated with a PEP?", "select", options=["no", "yes"])], "integration": "sanctions"},
                {"title": "Employment, income & affordability", "description": "Collect employment, income, household costs, debt and dependants.", "fields": [PRIVATE_COMMON_EMPLOYMENT, field("monthly_income", "Monthly income (PLN)", "number"), field("monthly_expenses", "Monthly household expenses (PLN)", "number"), field("monthly_debt_payments", "Monthly debt payments (PLN)", "number"), field("dependants", "Dependants", "number")], "integration": None},
                {"title": "BIK-style credit bureau & decision", "description": "Run a deterministic BIK-style credit-bureau and affordability decision.", "fields": [field("credit_scenario", "Demo BIK credit scenario", "select", options=["good", "manual_review", "fail"])], "integration": "credit"},
                {"title": "Review summary, accept terms & submit", "description": "Review the application, accept the terms and submit.", "fields": [field("terms", "I confirm that the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
        "business": {
            "title": "Poland — Business",
            "steps": [
                {"title": "Company details", "description": "Collect NIP, REGON or KRS/CEIDG identifier and legal form.", "fields": [field("nip", "NIP"), field("regon", "REGON", required=False), field("krs_ceidg", "KRS/CEIDG", required=False), field("legal_form", "Legal form", "select", options=["sp_zoo", "sa", "sole_proprietor"])], "integration": "registry"},
                {"title": "Board member / sole proprietor authority", "description": "Confirm who can act for the company and their authority.", "fields": [field("representative_name", "Representative / board member"), field("authority", "Authority", "select", options=["authorised", "unknown"])], "integration": "representative"},
                {"title": "Beneficial owners & risk", "description": "Collect UBO ownership and run identity/risk and sanctions screening.", "fields": [field("ubo_name", "UBO name"), field("ubo_ownership", "Ownership (%)", "number"), field("pep_declared", "Is the UBO a PEP or closely associated with a PEP?", "select", options=["no", "yes"])], "integration": "ubo_kyc_sanctions"},
                {"title": "VAT/tax, activity & expected usage", "description": "Capture VAT/tax status, business activity and expected usage.", "fields": [field("vat_status", "VAT/tax status", "select", options=["valid", "manual", "invalid"]), field("activity", "Business activity"), field("expected_usage", "Expected usage"), field("annual_turnover", "Annual turnover (PLN)", "number")], "integration": "business_profile"},
                {"title": "KYB, sanctions/PEP, business credit & bank account", "description": "Run company credit/risk and bank-account validation.", "fields": [field("business_risk", "Demo business risk", "select", options=["good", "manual_review", "fail"]), field("iban", "IBAN"), field("account_name", "Account holder name"), field("bank_scenario", "Demo bank scenario", "select", options=["verified", "name_mismatch", "unreachable"])], "integration": "business_final"},
                {"title": "Review & sign", "description": "Review the business application, accept the terms and sign/submit.", "fields": [field("terms", "I confirm the information is correct and accept the terms", "checkbox")], "integration": None},
            ],
        },
    },
}
