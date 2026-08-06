import requests



def send_whatsapp_message(message):


    """
    Send WhatsApp message using Meta Cloud API

    Credentials will be added later
    """



    phone_number_id = "YOUR_PHONE_NUMBER_ID"

    access_token = "YOUR_ACCESS_TOKEN"


    receiver_number = "RECIPIENT_NUMBER"



    url = (
        f"https://graph.facebook.com/v20.0/"
        f"{phone_number_id}/messages"
    )



    headers = {

        "Authorization":
        f"Bearer {access_token}",

        "Content-Type":
        "application/json"

    }



    payload = {


        "messaging_product":
        "whatsapp",


        "to":
        receiver_number,


        "type":
        "text",


        "text":
        {

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



        if response.status_code == 200:


            print(
                "WhatsApp Message Sent Successfully"
            )


        else:


            print(
                "WhatsApp Error:"
            )


            print(
                response.text
            )



    except Exception as e:


        print(
            "WhatsApp Connection Error:",
            e
        )