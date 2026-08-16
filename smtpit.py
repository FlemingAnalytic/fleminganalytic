import smtplib, ssl
from email.message import EmailMessage
from email.utils import formataddr,make_msgid
import uuid
import os
def mailit(to_name,to_email,subject, message):
 try:
    port = 587
    smtp_server = "smtp.zeptomail.com"
    username="emailapikey"
    # No default: a live sending key used to sit here, and a fallback that
    # works without configuration is a fallback nobody notices until it is
    # published somewhere it should not be.
    password = os.getenv("EMAIL_PWD")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(("Fleming Analytic", "noreply@fleminganalytic.com"))
    msg['To'] = formataddr((to_name, to_email))
    msg_id = make_msgid(domain="fleminganalytic.com")
    msg['Message-ID'] = msg_id
    msg.add_alternative(message, subtype='html')
    with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    print ("successfully sent")
 except Exception as e:
    print (e.message)

#order='''
#<h1>Order Details</h1>
#       <p><ul>
#       <li><span><b>XYZ</b> $100</span>
#       
#       <ul>
#         <li><span>opt1 $.24 </li></span>
#         <li><span>opt2 </li></span>
#       </ul>
#       </li>
#       </ul>
#       
#       </p>
#'''
#mailit("John Doe","johnflem@hotmail.com","Order Confirmation",order)