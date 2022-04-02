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


class MockBuild:

    def buildTransaction(self, *args, **kwargs):
        return None


class MockedAllowed:

    class functions:
        def allowance(self, *args, **kwargs):
            return CallClass

        def approve(self, *args, **kwargs):
            return MockBuild()

class MockedNotAllowed:

    class functions:
        def allowance(self, *args, **kwargs):
            return CallClassZero


class MockedOwner:

    class functions:
        def ownerOf(self, *args, **kwargs):
            return CallOwner()