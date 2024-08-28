class TokensUnavailableException(Exception):
    """Exception for tokens' checker."""

    def __init__(self, token_name):
        """Reinitializing message atribute."""
        self.message = f'''
        {token_name} token(s) is None!
        Make sure that it is identified in local .env file'''
        super().__init__(self.message)


class UnexpectedStatusError(Exception):
    """Exception for unexpected status from API."""

    def __init__(self, unexpected_status):
        """Reinitializing message atribute."""
        self.message = f'''
        {unexpected_status} status is unexpected!
        Impossible to parse it, check API for changes!'''
        super().__init__(self.message)


class UnexpectedArgException(Exception):
    """Exception for unexpected argument in API request."""

    def __init__(self):
        """Reinitializing message atribute."""
        self.message = 'Unexpected argument in request!'
        super().__init__(self.message)


class TokenError(Exception):
    """Exception for wrong Practicum token."""

    def __init__(self):
        """Reinitializing message atribute."""
        self.message = '''
        Personal token is incorrect!
        Check token in .env file!
        '''
        super().__init__(self.message)


class NoUpdatesException(Exception):
    """Exception for no updates on statuses."""

    def __init__(self, last_status):
        """Reinitializing message atribute."""
        self.message = f'''
        No new statuses!
        Last status is {last_status}!
        '''
        super().__init__(self.message)


class NoHWDict(Exception):
    """Exception for no HW dict in API response."""

    def __init__(self):
        """Reinitializing message atribute."""
        self.message = '''
        No HW dict in API response!
        Something went wrong!
        '''
        super().__init__(self.message)


class NoHWName(Exception):
    """Exception for no HW name in dict in response."""

    def __init__(self):
        """Reinitializing message atribute."""
        self.message = '''
        No key homework_name in response dict in!
        Something went wrong!
        '''
        super().__init__(self.message)


class EmptyResponseList(Exception):
    """Exception for no Empty Response List."""

    def __init__(self):
        """Reinitializing message atribute."""
        self.message = '''
        Response List is empty!
        Something went wrong!
        '''
        super().__init__(self.message)