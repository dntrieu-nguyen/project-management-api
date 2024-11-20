from django.core.mail import send_mail
def send_email(subject, txt_,from_email, recipient_list, html_):
    # validate ???

    action_send_mail = send_mail(
                subject,
                txt_,
                from_email,
                recipient_list.split(','), # format 'admin@gmail.com,admin@example.com'
                html_message=html_,
                fail_silently=False,
            )
    
    return action_send_mail