import unittest

from ssh_auther.ssh.remote import build_authorized_keys_payload


class BuildAuthorizedKeysPayloadTests(unittest.TestCase):
    def test_adds_separator_when_existing_file_lacks_trailing_newline(self):
        payload = build_authorized_keys_payload("existing-key", "ssh-ed25519 AAAATEST comment")
        self.assertEqual(payload, "\nssh-ed25519 AAAATEST comment\n")

    def test_appends_single_newline_for_empty_file(self):
        payload = build_authorized_keys_payload("", "ssh-ed25519 AAAATEST comment")
        self.assertEqual(payload, "ssh-ed25519 AAAATEST comment\n")

    def test_rejects_blank_key_line(self):
        with self.assertRaises(ValueError):
            build_authorized_keys_payload("existing\n", "   ")


if __name__ == "__main__":
    unittest.main()
