def send_htmltext(user, content):

    message = MIMEMultipart("alternative")
    message["Subject"] = content['subject']
    message["From"] = sender_email
    message["To"] = user.email

    print("\nMESSAGE IS:\n")
    print(message)

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(content['text'], "plain")
    part2 = MIMEText(content['html'], "html")

    print("\nMESSAGE PARTS\n")
    # print(part1)
    # print(part2)

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    print("\nMESSAGE ATTACHMENT\n")
    # print(message)

    # Create secure connection with server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, message['To'], message.as_string()
        )

        print("\nIS DONE\n")

    print("\nDONE CODE EXECUTION\n")

    return None

