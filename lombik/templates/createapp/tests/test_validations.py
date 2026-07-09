def test_password_strength_validation():
    from lombik.validation import validate_password_strength
    
    invalid_cases = [
        "1234567",
        "testpassword",
        "TESTPASSWORD",
        "TestPassword",
        "testpassword@",
        "TestPassword123"
    ]

    valid_cases = [
        "Test123!",
        "TestPassword@123",
        "ThisIsOkay--123@@__"
    ]

    
    for case in invalid_cases:
        res = validate_password_strength(case)
        assert res.success == False

    for case in valid_cases:
        res = validate_password_strength(case)
        assert res.success == True


def test_email_pattern_validation():
    from lombik.validation import valid_email_pattern
    invalid_cases = [
        "test.at.com",
        "example@gmail@gmail.com",
        "@gmail.com",
        "example.@.gmail.com",
        "examplegmail.com",
        "example@",
        "@example.com",
        "example..test@gmail.com",
        "example@google..com",
        ".example@gmail.com",
        "example.@gmail.com",
        "example@.gmail.com",
        "example@gmail.com.",
        "exa mple@gmail.com",
        "example@gm ail.com",
        "example@com",
        "example@gmail",
        "exa@mple@gmail.com",
        "example@@gmail.com",
        "example@exam\u200Bple.com",
    ]

    valid_cases = [
        "example@gmail.com",
        "test123@gmail.com.au",
        "test+filter@gmail.com",
        "user.name+tag@gmail.com",
        "user@mail.google.com",
        "test@sub.mail.google.com",
        "test@my-domain.com",
        "user@domain.io",
        "user@domain.tech",
        "a.b.c.d@gmail.com",
    ]

    for case in invalid_cases:
        assert valid_email_pattern(case) == False


    for case in valid_cases:
        assert valid_email_pattern(case) == True


def test_role_validation():
    from lombik.validation import validate_role

    invalid_cases = [
        None, "", "somelongstringthatwillneveroccurinroles"
    ]

    for case in invalid_cases:
        assert validate_role(case) == False