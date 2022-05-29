import axie_utils


def test_version():
    assert axie_utils.__version__ == '2.1.1'


def test_init():
    assert axie_utils.__all__ == [
    'Axies',
    'AxieGraphQL',
    'Breed',
    'Claim',
    'CustomUI',
    'Morph',
    'Payment',
    'Scatter',
    'Transfer',
    'TrezorAxieGraphQL',
    'TrezorBreed',
    'TrezorClaim',
    'TrezorConfig',
    'TrezorMorph',
    'TrezorPayment',
    'TrezorScatter',
    'TrezorTransfer',
    'get_nonce',
    'get_lastclaim',
    'check_balance']
