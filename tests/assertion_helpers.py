def assert_send_grid_mock_send(mock_send,
                               receivers,
                               *,
                               num_of_calls=1,
                               bccs=None):
    bccs = bccs if bccs else []
    assert mock_send.called
    assert mock_send.call_count == num_of_calls
    if isinstance(receivers, str):
        receivers = [receivers]
    mail_obj = mock_send.call_args[0][0]
    personalization = mail_obj.personalizations[0]
    emails = [person['email'] for person in personalization.tos]
    assert emails == receivers
    if bccs:
        for email_obj in personalization.bccs:
            assert email_obj['email'] in bccs

    return mail_obj.contents[0].content
