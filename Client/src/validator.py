# Ben Ryan C15507277

import string


class Validator():
    def __init__(self):
        self.lowercase = list(string.ascii_lowercase)
        self.uppercase = list(string.ascii_uppercase)
        self.digits = list(string.digits)
        self.whitespace = list(string.whitespace)
        self.special = list(string.punctuation)
        self.hexdigits = list(string.hexdigits)
        self.allValid = list(string.printable)

    def validateUsername(self, username):
        valid = True
        msg = ''

        if username is None or username == '':
            valid = False
            msg += '\n\tMust not be blank'

        if len(username) < 5:
            valid = False
            msg += '\n\tMust be at least 5 characters long'
        elif len(username) > 32:
            valid = False
            msg += '\n\tMust be no more than 32 characters long'

        if any(char in username for char in self.whitespace):
            valid = False
            msg += '\n\tMust not contain whitespace'

        if any(char in username for char in self.special):
            valid = False
            msg += '\n\tMust not contain speical characters'

        for char in username:
            if char not in self.allValid:
                valid = False
                msg = '\n\tInvalid character: ' + char
                break

        return valid, msg

    def validatePassword(self, password, passConf, username):
        valid = True
        msg = ''

        if password is None or password == '':
            valid = False
            msg += '\n\tMust not be blank'

        if password != passConf:
            valid = False
            msg += '\n\tConfirmation password does not match'

        if len(password) < 8:
            valid = False
            msg += '\n\tMust be at least 8 characters long'

        elif len(password) > 128:
            valid = False
            msg += '\n\tMust not be no more than 128 characters long'

        if username in password:
            valid = False
            msg += '\n\tMust not contain username'

        if not any(char in password for char in self.lowercase):
            valid = False
            msg += '\n\tMust contain at least one lowercase letter'

        if not any(char in password for char in self.uppercase):
            valid = False
            msg += '\n\tMust contain at least one uppercase letter'

        if not any(char in password for char in self.digits):
            valid = False
            msg += '\n\tMust contain at least one digit'

        if not any(char in password for char in self.special):
            valid = False
            msg += '\n\tMust contain at least one special character'

        if any(char in password for char in self.whitespace):
            valid = False
            msg += '\n\tMust not contain whitespace'

        for char in password:
            if char not in self.allValid:
                valid = False
                msg = '\n\tInvalid character: ' + char
                break

        return valid, msg

    def validateEmail(self, email):
        valid = True
        msg = ''

        if email is None or email == '':
            valid = False
            msg += '\n\tMust not be blank'
        else:
            parts = email.split('@')
            if len(parts) != 2:
                valid = False
                msg += '\n\tInvalid structure regarding @'
            else:
                prefix = parts[0]
                domain = parts[1]

                if prefix == '':
                    valid = False
                    msg += '\n\tBlank prefix'

                if domain == '':
                    valid = False
                    msg += '\n\tBlank Domain'

                parts = domain.split('.')

                if len(parts) != 2 or parts[0] == '' or parts[1] == '':
                    valid = False
                    msg += '\n\tInvalid Domain'

        if len(email) > 254:
            valid = False
            msg += "\n\tMust not exceed 254 characters"

        return valid, msg

    def validateKey(self, key):
        valid = True
        msg = ''

        if key is None or key == '':
            valid = False
            msg += '\n\tMust not be blank'

        if len(key) != 32:
            valid = False
            msg += '\n\tMust be exactly 32 characters long'

        for char in key:
            if char not in self.hexdigits:
                valid = False
                msg += '\n\tInvalid Character: ' + char
                break

        return valid, msg
