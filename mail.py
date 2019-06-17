import email
import imaplib
from datetime import datetime, timedelta
from json import load


class ImapWrapper:

    mail = None
    utility = None

    def __init__(self,smtp_server):
        self.mail = imaplib.IMAP4_SSL(smtp_server)
        self.utility = Utility()
        pass

    def login(self,username:str , password : str) :
        self.mail.login(username, password)
        pass

    def list_mail_boxes(self):
        mailbox = self.mail.list()
        boxes = []
        for item in mailbox[1]:
            flags , box = self.utility.extract_mail_box(item.decode())
            if "\\Noselect" not in flags:
                boxes.append(box)
        return boxes

    def select_mail_box(self,inbox_name):
        self.mail.select(inbox_name)

    def fetch_mail(self,uid):
        result, data = self.mail.fetch(uid,'(RFC822)')
        return self.utility.extract_body(data)
        pass

    def search(self, unread = True , since = (datetime.now() - timedelta(days=180)), before = None , sender = None):
        args = []

        if unread:
            args.append('UNSEEN')
        if since is not None:
            args.append('SINCE')
            args.append(since.strftime('%d-%b-%Y'))
        if before is not None:
            args.append('BEFORE')
            args.append(before.strftime('%d-%b-%Y'))
        if sender is not None:
            args.append('FROM')
            args.append(sender)

        result , data = self.mail.search(None,*args)
        if result == 'OK':
            return data[0].decode().split()
        return []

    def __del__(self):
        if self.mail is not None:
            try:
                self.mail.close()
            except:
                pass
        pass



class Utility:

    def extract_body(self,data):
        response = {'attachments':[]};
        for response_part in data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes((response_part[1]))
                for m in msg.walk():
                    response['subject'] = response.get('subject') or m['subject']
                    response['from'] = response.get('from') or m['from']
                    response['msg_id'] = response.get('msg_id') or m['Message-Id']
                    response['recv_date'] = response.get('recv_date') or m['Date']
                    content = m.get_payload(decode=True)



                    if content is not None:
                        if m.get_content_type() != 'application/octet-stream':
                           response['content_type'] = m.get_content_type()
                           response['text']=content.decode("utf-8",errors="ignore" )
                        else:
                            f = open(m.get_filename(),'wb')
                            f.write(content)
                            f.close()
                            response['attachments'].append(m.get_filename())
        return response

    def extract_mail_box(self,mail_box_response):
        # Format : flags, the hierarchy delimiter, and mailbox name
        flags = ""
        delimiter = None
        mailbox_name = ""
        _flag_start = False

        for ch in mail_box_response:
            if ch == '(':
                _flag_start = True
                continue
            if ch == ')':
                _flag_start= False
                continue
            if ch == '\"':
                continue
            if _flag_start:
                flags+=ch
                continue
            if delimiter is None and ch != ' ':
                delimiter = ch
                pass
            else:
                mailbox_name+=ch
            pass
        return flags,'"'+mailbox_name.strip()+'"'

if __name__ == '__main__':
    m = ImapWrapper("imap.gmail.com")

    credentials = {}
    with open('credentials.json', 'rt', encoding='utf-8') as f:
        credentials = load(f)
    m.login(credentials['e'],credentials['pe'])
    m.select_mail_box('"Inbox"')
    ids = m.search()
    for x in ids:
        content = m.fetch_mail(x)

        print(content)
        # rfc822msgid:
