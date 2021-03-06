import email

import boto
from boto.exception import BotoServerError

import sure  # noqa

from moto import mock_ses


@mock_ses
def test_verify_email_identity():
    conn = boto.connect_ses('the_key', 'the_secret')
    conn.verify_email_identity("test@example.com")

    identities = conn.list_identities()
    address = identities['ListIdentitiesResponse']['ListIdentitiesResult']['Identities'][0]
    address.should.equal('test@example.com')


@mock_ses
def test_domain_verify():
    conn = boto.connect_ses('the_key', 'the_secret')

    conn.verify_domain_dkim("domain1.com")
    conn.verify_domain_identity("domain2.com")

    identities = conn.list_identities()
    domains = list(identities['ListIdentitiesResponse']['ListIdentitiesResult']['Identities'])
    domains.should.equal(['domain1.com', 'domain2.com'])


@mock_ses
def test_delete_identity():
    conn = boto.connect_ses('the_key', 'the_secret')
    conn.verify_email_identity("test@example.com")

    conn.list_identities()['ListIdentitiesResponse']['ListIdentitiesResult']['Identities'].should.have.length_of(1)
    conn.delete_identity("test@example.com")
    conn.list_identities()['ListIdentitiesResponse']['ListIdentitiesResult']['Identities'].should.have.length_of(0)


@mock_ses
def test_send_email():
    conn = boto.connect_ses('the_key', 'the_secret')

    conn.send_email.when.called_with(
        "test@example.com", "test subject",
        "test body", "test_to@example.com").should.throw(BotoServerError)

    conn.verify_email_identity("test@example.com")
    conn.send_email("test@example.com", "test subject", "test body", "test_to@example.com")

    send_quota = conn.get_send_quota()
    sent_count = int(send_quota['GetSendQuotaResponse']['GetSendQuotaResult']['SentLast24Hours'])
    sent_count.should.equal(1)


@mock_ses
def test_send_raw_email():
    conn = boto.connect_ses('the_key', 'the_secret')

    to = 'to@example.com'
    message = email.mime.multipart.MIMEMultipart()
    message['Subject'] = 'Test'
    message['From'] = 'test@example.com'
    message['To'] = to

    # Message body
    part = email.mime.text.MIMEText('test file attached')
    message.attach(part)

    # Attachment
    part = email.mime.text.MIMEText('contents of test file here')
    part.add_header('Content-Disposition', 'attachment; filename=test.txt')
    message.attach(part)

    conn.send_raw_email.when.called_with(
        source=message['From'],
        raw_message=message.as_string(),
        destinations=message['To']
    ).should.throw(BotoServerError)

    conn.verify_email_identity("test@example.com")
    conn.send_raw_email(
        source=message['From'],
        raw_message=message.as_string(),
        destinations=message['To']
    )

    send_quota = conn.get_send_quota()
    sent_count = int(send_quota['GetSendQuotaResponse']['GetSendQuotaResult']['SentLast24Hours'])
    sent_count.should.equal(1)
