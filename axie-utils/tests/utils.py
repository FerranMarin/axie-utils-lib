from hexbytes import HexBytes


class MockedSignedMsg:

    def __init__(self):
        self.signature = HexBytes(b'123')


class CallClass:

    def call():
        return 123


class CallClassZero:

    def call():
        return 0


class CallOwner:

    def call(*args, **kwargs):
        return "0xabc123"


class MockedAllowed:

    class functions:
        def allowance(self, *args, **kwargs):
            return CallClass


class MockedNotAllowed:

    class functions:
        def allowance(self, *args, **kwargs):
            return CallClassZero


class MockedOwner:

    class functions:
        def ownerOf(self, *args, **kwargs):
            return CallOwner()