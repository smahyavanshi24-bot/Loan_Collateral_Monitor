from modules.whatsapp_alert import generate_alert


record = {

    "date":"05-Aug-2026",

    "borrower":"Everbest",

    "security":"JSW Energy",

    "cover":1.19,

    "required_cover":1.50,

    "status":"❌ Shortfall"

}



message = generate_alert(record)


print(message)