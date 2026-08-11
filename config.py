# -*- coding: utf-8 -*-

# =====================================================
# LOAN COLLATERAL MONITORING SYSTEM
# CONFIGURATION FILE
# =====================================================


# =====================================================
# BORROWER & SECURITY CONFIGURATION
# =====================================================

BORROWERS = [

    {
        "name": "Everbest",

        "loan_amount": 1200000000,

        "total_required_cover": 2.00,

        "securities": [

            {
                "name": "JSW Energy",

                "symbol": "JSWENERGY.NS",

                "shares": 2533300,

                "required_cover": 1.00
            },

            {
                "name": "JSW Steel",

                "symbol": "JSWSTEEL.NS",

                "shares": 1096000,

                "required_cover": 1.00
            }

        ]
    },


    {
        "name": "Siddeshwari",

        "loan_amount": 2500000000,

        "total_required_cover": 2.00,

        "securities": [

            {
                "name": "JSW Energy",

                "symbol": "JSWENERGY.NS",

                "shares": 9200000,

                "required_cover": 1.50
            },

            {
                "name": "Jindal Steel & Power",

                "symbol": "JINDALSTEL.NS",

                "shares": 1600000,

                "required_cover": 0.50
            }

        ]
    }

]


# =====================================================
# WHATSAPP CLOUD API CONFIGURATION
# =====================================================

# Meta WhatsApp Business Phone Number ID

WHATSAPP_PHONE_ID = (
    "1178023992071733"
)


# IMPORTANT:
# Put your NEWLY ROTATED Meta access token here.
#
# The previous token you pasted into this chat should
# be revoked/rotated because it has been exposed.

WHATSAPP_ACCESS_TOKEN = (
    "EAArFnYOyg90BSFzxwvIS1hZAGRlKHaSUBGhqiEfEUfo0Yn8eUTmZCiYXo8C0QvZAyKA5DSZB0ZCSJ68SlmhCuLY6KETDizzLgZAwGphEhoxtpvj0BzHktDCLS61F2c2wf1TGsWPXQEj2OOOMN1bvSgehsxxCAzIsdJqCJUApT9MEOGwZCz2h0KQ8k3I9waPhUDG0opRZB1qQmaCZBarLj4nzMYv6ulZB0yZCKe3bAOtpdD2cCBQqUoFbXjyLlavns5ek6SGeAqnmVFj0ZBIrE0wvS3QJ6OgU"
)


# =====================================================
# WHATSAPP RECEIVERS
# =====================================================

WHATSAPP_RECEIVERS = (

    "918655714690",

    "919967807134",

    "917710076331"

)


# =====================================================
# SYSTEM SETTINGS
# =====================================================

REPORT_FOLDER = "reports"

DATABASE_FOLDER = "database"

LOG_FOLDER = "logs"