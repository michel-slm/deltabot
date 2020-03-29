
from deltabot.bot import Replies


class TestDeltaBot:
    def test_self_contact(self, mock_bot):
        contact = mock_bot.self_contact
        assert contact.addr
        assert contact.display_name
        assert contact.id

    def test_get_contact(self, mock_bot):
        contact = mock_bot.get_contact("x@example.org")
        assert contact.addr == "x@example.org"
        assert contact.display_name == "x@example.org"

        contact2 = mock_bot.get_contact(contact)
        assert contact2 == contact

        contact3 = mock_bot.get_contact(contact.id)
        assert contact3 == contact

    def test_get_chat(self, mock_bot):
        chat = mock_bot.get_chat("x@example.org")
        contact = mock_bot.get_contact("x@example.org")
        assert contact.get_chat() == chat
        assert mock_bot.get_chat(contact) == chat
        assert mock_bot.get_chat(chat.id) == chat

        msg = chat.send_text("hello")
        assert mock_bot.get_chat(msg) == chat

    def test_create_group(self, mock_bot):
        members = set(["x{}@example.org".format(i) for i in range(3)])
        chat = mock_bot.create_group("test", members=members)
        assert chat.get_name() == "test"
        assert chat.is_group()
        for contact in chat.get_contacts():
            members.discard(contact.addr)
        assert not members


class TestReplies:
    def test_two_text(self, mock_bot):
        r = Replies(mock_bot.account)
        r.add(text="hello")
        r.add(text="world")
        l = list(r.get_reply_messages())
        assert len(l) == 2
        assert l[0].text == "hello"
        assert l[1].text == "world"

    def test_file(self, mock_bot, tmpdir):
        p = tmpdir.join("textfile")
        p.write("content")
        r = Replies(mock_bot.account)
        r.add(text="hello", filename=p.strpath)
        l = list(r.get_reply_messages())
        assert len(l) == 1
        assert l[0].text == "hello"
        s = open(l[0].filename).read()
        assert s == "content"
