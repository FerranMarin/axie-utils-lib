import axie_utils


def test_version():
    assert axie_utils.__version__ == '1.0.1'


def test_init():
    assert axie_utils.__all__ == [
        'Axies',
        'AxieGraphQL',
        'Breed',
        'Claim',
        'CustomUI',
        'Morph',
        'Payment',
        'Transfer',
        'TrezorAxieGraphQL',
        'TrezorBreed',
        'TrezorClaim',
        'TrezorMorph',
        'TrezorPayment',
        'TrezorTransfer',
        'get_nonce',
        'check_balance']
