# =====================================================
# LOAN COLLATERAL MONITORING SYSTEM
# WHATSAPP ALERT MODULE
# =====================================================

from datetime import datetime
import requests

from config import (
    WHATSAPP_PHONE_ID,
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_RECEIVERS
)


# =====================================================
# Generate Daily Summary
# =====================================================

def generate_daily_summary(records):

    date = datetime.now().strftime("%d-%b-%Y")

    message = []

    message.append(
        "📊 COLLATERAL MONITORING REPORT"
    )

    message.append(
        f"\nDate: {date}"
    )

    message.append(
        "\n----------------------------"
    )


    for record in records:

        message.append(
            f"""

Borrower:
{record['borrower']}

Security:
{record['security']}

Current Cover:
{record['cover']:.2f}x

Required Cover:
{record['required_cover']:.2f}x

Status:
{record['status']}

----------------------------
"""
        )


    return "\n".join(message)



# =====================================================
# Generate Shortfall Alert
# =====================================================

def generate_alert(record):

    if "Shortfall" in record["status"]:


        shortfall = (
            record["required_cover"]
            -
            record["cover"]
        )


        message = f"""
🚨 COLLATERAL SHORTFALL ALERT

Date:
{record['date']}

Borrower:
{record['borrower']}

Security:
{record['security']}

Current Cover:
{record['cover']:.2f}x

Required Cover:
{record['required_cover']:.2f}x

Shortfall:
{shortfall:.2f}x

Action Required:
Please review collateral immediately.
"""


        return message


    return None



# =====================================================
# SEND WHATSAPP ALERT TO MULTIPLE NUMBERS
# =====================================================

def send_whatsapp_alert(message):


    url = (
        f"https://graph.facebook.com/v22.0/"
        f"{WHATSAPP_PHONE_ID}/messages"
    )


    headers = {

        "Authorization":
        f"Bearer {WHATSAPP_ACCESS_TOKEN}",

        "Content-Type":
        "application/json"

    }



    for receiver in WHATSAPP_RECEIVERS:


        payload = {

            "messaging_product":
            "whatsapp",

            "recipient_type":
            "individual",

            "to":
            receiver,

            "type":
            "text",

            "text":
            {

                "preview_url":
                False,

                "body":
                message

            }

        }



        try:


            response = requests.post(

                url,

                headers=headers,

                json=payload

            )


            print("\n==============================")

            print(
                "WhatsApp Recipient:",
                receiver
            )


            print(
                "Status Code:",
                response.status_code
            )


            print(
                "Response:"
            )


            print(
                response.text
            )



            if response.status_code == 200:

                print(
                    "✅ Message Accepted"
                )

            else:

                print(
                    "❌ Message Failed"
                )



        except Exception as e:


            print(
                "❌ WhatsApp Error for:",
                receiver
            )


            print(e)