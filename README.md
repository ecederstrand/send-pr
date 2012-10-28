send-pr
=======

Python script to import send-pr emails to Bugzilla.

Takes a send-pr email from stdin and pushes it into Bugzilla, including adding attachments 
to the bug. It relies on the Bugzilla XML-RPC API.

It needs to be adjusted to the actual Bugzilla setup (severity state names etc.) and how 
you want to map send-pr fields to Bugzilla fields.

To make it process emails sent to a given email address, stick it into /etc/mail/aliases like this:

    freebsd-gnats-submit:   "|/path/to/send_pr_to_bugzilla.py"
