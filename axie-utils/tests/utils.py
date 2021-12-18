from hexbytes import HexBytes


class MockedSignedMsg:

    def __init__(self):
        self.signature = HexBytes(b'123')
