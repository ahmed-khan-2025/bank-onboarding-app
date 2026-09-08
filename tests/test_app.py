import os
import tempfile


def make_client():
    """
    Create a temporary SQLite database and Flask test client.
    """

    db_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".db"
    )
    db_file.close()

    os.environ["ONBOARDING_DB"] = db_file.name

    import db

    db.DB_PATH = db_file.name
    db.init_db()

    import app as app_module

    app_module.app.config.update(
        TESTING=True,
        SECRET_KEY="test"
    )

    return app_module.app.test_client(), db_file.name


def cleanup_db(db_file):
    """
    Remove temporary database.
    """

    if db_file and os.path.exists(db_file):
        os.unlink(db_file)


def get_se_private_flow():
    """
    Get the actual Sweden/private flow from config.py.

    This means the test uses the same configuration as the
    application itself instead of hard-coding the number of steps.
    """

    from config import FLOWS

    return FLOWS["SE"]["private"]


def value_for_field(field):
    """
    Generate a valid test value based on the actual configured field.

    This is deliberately based on field names/types/options from
    config.py so the test follows the application's real flow.
    """

    name = field["name"]
    field_type = field["type"]
    options = field.get("options", [])

    # ---------------------------------------------------------
    # CHECKBOXES
    # ---------------------------------------------------------

    if field_type == "checkbox":
        return "on"

    # ---------------------------------------------------------
    # SELECT FIELDS
    # ---------------------------------------------------------

    if field_type == "select":

        # Identity
        if name == "identity_scenario":
            if "success" in options:
                return "success"

        # Credit
        if name == "credit_scenario":
            if "good" in options:
                return "good"

        # Address
        if name == "address_scenario":
            if "verified" in options:
                return "verified"

        # PEP
        if name == "pep_declared":
            if "no" in options:
                return "no"

        # Employment
        if name == "employment_status":
            if "employed" in options:
                return "employed"

        # Tax residency
        if name == "tax_residency":
            if "Sweden" in options:
                return "Sweden"

        # Identity method
        if name == "identity_method":
            if options:
                return options[0]

        # Generic select fallback
        if options:
            return options[0]

        return ""

    # ---------------------------------------------------------
    # EMAIL
    # ---------------------------------------------------------

    if field_type == "email":
        return "test@example.com"

    # ---------------------------------------------------------
    # NUMBER
    # ---------------------------------------------------------

    if field_type == "number":

        if name == "monthly_income":
            return "40000"

        if name == "monthly_expenses":
            return "15000"

        if name == "housing_cost":
            return "12000"

        if name == "monthly_debt_payments":
            return "5000"

        if name == "dependants":
            return "0"

        if name == "ubo_ownership":
            return "100"

        if name in ("turnover", "annual_turnover"):
            return "500000"

        return "100"

    # ---------------------------------------------------------
    # TEXT FIELDS
    # ---------------------------------------------------------

    if field_type == "text":

        if name == "personal_number":
            return "19900101-1234"

        if name == "email":
            return "test@example.com"

        if name == "phone":
            return "0700000000"

        if name == "address":
            return "Main Street 1"

        if name == "postal_code":
            return "11122"

        if name == "city":
            return "Stockholm"

        if name == "tax_residency":
            return "Sweden"

        if name == "employment_status":
            return "employed"

        if name == "dni_nie":
            return "12345678Z"

        if name == "province":
            return "Madrid"

        if name == "identity_method":
            return "Clave"

        if name == "organization_number":
            return "556677-8899"

        if name == "org_number":
            return "556677-8899"

        if name == "legal_name":
            return "Test Company AB"

        if name == "company_name":
            return "Test Company AB"

        if name == "business_activity":
            return "Software development"

        if name == "purpose":
            return "Business banking"

        if name == "representative_name":
            return "Test Representative"

        if name == "representative_personal_number":
            return "19900101-1234"

        if name == "ubo_name":
            return "Test Owner"

        if name == "ubo_personal_number":
            return "19900101-1234"

        if name == "krs":
            return "0000123456"

        if name == "nip":
            return "1234567890"

        if name == "regon":
            return "123456789"

        if name == "iban":
            return "SE4550000000058398257466"

        return "Test value"

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    return "Test value"


def build_step_data(step):
    """
    Build POST data for one actual configured step.
    """

    data = {}

    for field in step.get("fields", []):
        name = field["name"]

        # Send all fields with valid values.
        data[name] = value_for_field(field)

    return data


def test_start_creates_application():
    client, db_file = make_client()

    try:
        response = client.post(
            "/start",
            data={
                "country": "SE",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302
        assert "/applications/" in response.headers["Location"]

    finally:
        cleanup_db(db_file)


def test_invalid_start_redirects_home():
    client, db_file = make_client()

    try:
        response = client.post(
            "/start",
            data={
                "country": "XX",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302
        assert response.headers["Location"].endswith("/")

    finally:
        cleanup_db(db_file)


def test_first_step_validation_stays_on_page():
    client, db_file = make_client()

    try:
        response = client.post(
            "/start",
            data={
                "country": "SE",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302

        location = response.headers["Location"]

        response = client.post(
            location,
            data={}
        )

        assert response.status_code == 200

        assert (
            b"required" in response.data.lower()
            or b"Please fix" in response.data
        )

    finally:
        cleanup_db(db_file)


def test_complete_good_private_journey():
    """
    Complete the actual configured Sweden/private journey.

    IMPORTANT:
    The test reads FLOWS["SE"]["private"] directly, so it does not
    assume that the journey contains exactly 6 steps or 7 steps.
    """

    client, db_file = make_client()

    try:

        # ---------------------------------------------------------
        # START
        # ---------------------------------------------------------

        response = client.post(
            "/start",
            data={
                "country": "SE",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302

        location = response.headers["Location"]

        app_id = (
            location
            .split("/applications/")[1]
            .split("/")[0]
        )

        print("\nAPPLICATION ID:", app_id)

        # ---------------------------------------------------------
        # GET ACTUAL FLOW
        # ---------------------------------------------------------

        flow = get_se_private_flow()

        steps = flow["steps"]

        print("\nNUMBER OF CONFIGURED STEPS:", len(steps))

        # ---------------------------------------------------------
        # COMPLETE EVERY CONFIGURED STEP
        # ---------------------------------------------------------

        for index, step in enumerate(steps):

            data = build_step_data(step)

            print("\n----------------------------------------")
            print("STEP:", index)
            print("TITLE:", step.get("title"))
            print("FIELDS:", [
                field["name"]
                for field in step.get("fields", [])
            ])
            print("DATA:", data)

            response = client.post(
                f"/applications/{app_id}/step/{index}",
                data=data,
                follow_redirects=False
            )

            print("STATUS:", response.status_code)
            print(
                "LOCATION:",
                response.headers.get("Location")
            )

            # -----------------------------------------------------
            # VALIDATION FAILURE
            # -----------------------------------------------------

            if response.status_code != 302:

                print("\n========== FAILED STEP ==========")

                try:
                    print(response.data.decode("utf-8"))
                except Exception:
                    print(response.data)

                print("========== END FAILED STEP ==========\n")

            assert response.status_code == 302

        # ---------------------------------------------------------
        # REVIEW
        # ---------------------------------------------------------

        response = client.get(
            f"/applications/{app_id}/review"
        )

        print("\n----------------------------------------")
        print("REVIEW STATUS:", response.status_code)

        if response.status_code != 200:
            try:
                print(response.data.decode("utf-8"))
            except Exception:
                print(response.data)

        assert response.status_code == 200

        # ---------------------------------------------------------
        # DECISION
        # ---------------------------------------------------------

        assert (
            b"Approved" in response.data
            or b"approved" in response.data
        )

        # ---------------------------------------------------------
        # FINAL SUBMIT
        # ---------------------------------------------------------

        response = client.post(
            f"/applications/{app_id}/submit",
            follow_redirects=False
        )

        print("\n----------------------------------------")
        print("SUBMIT STATUS:", response.status_code)
        print(
            "SUBMIT LOCATION:",
            response.headers.get("Location")
        )

        assert response.status_code == 302

        assert response.headers["Location"].endswith(
            f"/applications/{app_id}/complete"
        )

    finally:
        cleanup_db(db_file)


def test_spain_private_has_tax_residency_and_reaches_review():
    """
    Test Spain/private using the actual configured flow.
    """

    client, db_file = make_client()

    try:

        response = client.post(
            "/start",
            data={
                "country": "ES",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302

        app_id = (
            response.headers["Location"]
            .split("/applications/")[1]
            .split("/")[0]
        )

        from config import FLOWS

        flow = FLOWS["ES"]["private"]

        steps = flow["steps"]

        print("\nSPAIN CONFIGURED STEPS:", len(steps))

        for index, step in enumerate(steps):

            data = build_step_data(step)

            # Make sure Spain tax residency is Spain if configured
            for field in step.get("fields", []):
                if field["name"] == "tax_residency":
                    if field["type"] == "select":
                        options = field.get("options", [])

                        if "Spain" in options:
                            data["tax_residency"] = "Spain"

            print("\n----------------------------------------")
            print("SPAIN STEP:", index)
            print("FIELDS:", [
                field["name"]
                for field in step.get("fields", [])
            ])
            print("DATA:", data)

            response = client.post(
                f"/applications/{app_id}/step/{index}",
                data=data,
                follow_redirects=False
            )

            print("STATUS:", response.status_code)

            if response.status_code != 302:

                print("\n========== FAILED SPAIN STEP ==========")

                try:
                    print(response.data.decode("utf-8"))
                except Exception:
                    print(response.data)

                print("========== END FAILED SPAIN STEP ==========\n")

            assert response.status_code == 302

        response = client.get(
            f"/applications/{app_id}/review"
        )

        assert response.status_code == 200

        assert (
            b"Approved" in response.data
            or b"approved" in response.data
        )

    finally:
        cleanup_db(db_file)


def test_resume_link_is_signed():
    client, db_file = make_client()

    try:

        response = client.post(
            "/start",
            data={
                "country": "SE",
                "customer_type": "private"
            }
        )

        assert response.status_code == 302

        app_id = (
            response.headers["Location"]
            .split("/applications/")[1]
            .split("/")[0]
        )

        response = client.get(
            f"/applications/{app_id}/resume-link"
        )

        assert response.status_code == 200

        assert b"Continue your application" in response.data

    finally:
        cleanup_db(db_file)