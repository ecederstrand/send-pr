#!/usr/bin/env python
import sys
import email

valid_send_pr_keys = (
'Submitter-Id',
'Originator',
'Organization',
'Confidential',
'Synopsis',
'Severity',
'Priority',
'Category',
'Class',
'Release',
'Environment',
'Description',
'How-To-Repeat',
'Fix',
)
items = {}
item_key = None
item_value = None

attachments = {}
is_attachment = False
attachment_filename = None
attachment_content = ''

# Read email from stdin
msg = email.message_from_file(sys.stdin)
body = msg.get_payload()

# Parse send-pr email
for line in body.splitlines(True):
	if item_key is None and not line.startswith('>'): continue # Empty lines in top of email
	if line.startswith('>'):
		# Parse ">SETTING : VALUE" line
		item_key, sep, item_value = [s.strip() for s in line[1:].partition(':')]
		assert item_key in valid_send_pr_keys
		assert item_key not in items
		items[item_key] = item_value
		continue
	if line.startswith('--- ') and line.rstrip().endswith(' begins here ---'):
		# Start parsing an attachment
		assert is_attachment == False
		assert attachment_filename is None
		assert attachment_content == ''
		is_attachment = True
		attachment_filename = line.replace('--- ', '').replace(' begins here ---', '').strip()
		assert len(attachment_filename) > 0
		assert attachment_filename not in attachments
		attachments[attachment_filename] = ''
		continue
	if line.startswith('--- ') and line.rstrip().endswith(' ends here ---'):
		# Attachment ends
		assert attachment_filename == line.replace('--- ', '').replace(' ends here ---', '').strip()
		is_attachment = False
		attachment_filename = None
		attachment_content = ''
		continue
	if is_attachment:
		#Read attachment contents
		assert attachment_filename is not None
		attachments[attachment_filename] += line
		continue
	# Multi-line setting values
	items[item_key] += line.rstrip()

print msg

XMLAPI_URL = 'http://example.com/bugs/xmlrpc.cgi'
BZ_USER = 'anonymous@example.com'
BZ_PASS = 'anonymous'

import xmlrpclib
import gzip
import Cookie

class SessionTransport(xmlrpclib.Transport):
    def parse_response(self, response):
        # read response data from httpresponse, and parse it

        # Check for new http response object, else it is a file object
        if hasattr(response,'getheader'):
            if response.getheader("Content-Encoding", "") == "gzip":
                stream = GzipDecodedResponse(response)
            else:
                stream = response
            cookie = response.getheader('Set-Cookie')
            if cookie:
                self.sessioncookie = Cookie.SimpleCookie()
                self.sessioncookie.load(cookie)
        else:
            stream = response

        p, u = self.getparser()

        while 1:
            data = stream.read(1024)
            if not data:
                break
            if self.verbose:
                print "body:", repr(data)
            p.feed(data)

        if stream is not response:
            stream.close()
        p.close()

        return u.close()

    def send_request(self, connection, handler, request_body):
        if (self.accept_gzip_encoding and gzip):
            connection.putrequest("POST", handler, skip_accept_encoding=True)
            connection.putheader("Accept-Encoding", "gzip")
        else:
            connection.putrequest("POST", handler)
        if hasattr(self, 'sessioncookie'):
            cookie = self.sessioncookie.output(header='', sep=';')
            connection.putheader('Cookie', cookie)


bz = xmlrpclib.ServerProxy(XMLAPI_URL, transport=SessionTransport())
login = bz.User.login(dict(login=BZ_USER, password=BZ_PASS))
user_id = login.get('id')
if user_id: print 'login success:', login

bug = bz.Bug.create(dict(
	product = 'TestProduct',
	component = 'TestComponent',
	summary = items['Synopsis'],
	version = '9.0', #items['Release'], 
	description = items['Description'] + '\n\nReported by: ' + items['Originator'] + 
		' (' +  (msg['Reply-To'] or msg['From']) + ')', 
	op_sys = 'FreeBSD', #items['Environment'],
	platform = 'All', #items['Release'].strip().split(' ')[-1],
	priority = items['Priority'].capitalize(),
	severity = items['Severity'],
	#alias=...,
	#assigned_to =...,
	#cc = [user.strip() for user in msg['Cc']],
	comment_is_private = True if items['Confidential'] != 'no' else False,
	#groups=...,
	#qa_contact=...,
	#status=...,
	#resolution=...,
	#target_milestone=...,)
))
bug_id = bug.get('id')
if bug_id: print 'bug create success', bug

for key, val in attachments.iteritems():
	print 'add attachment', key, bz.Bug.add_attachment(dict(
		ids = [int(bug_id)],
		data = val,
		file_name = key,
		summary = 'Added by send-pr',
		content_type = 'text/plain',
		#comment = ...,
		is_patch = True,
		is_private = True if items['Confidential'] != 'no' else False,
	))

#items['Category']
#items['Class']
#items['How-To-Repeat']
#items['Fix']
