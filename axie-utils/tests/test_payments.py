from mock import patch, call

from axie_utils import Payment, TrezorPayment
from axie_utils.abis import SLP_ABI
from axie_utils.utils import SLP_CONTRACT


@patch("web3.eth.Eth.contract", return_value="contract")
@patch("web3.Web3.toChecksumAddress")
def test_payment_get_nonce_calls_w3_low_nonce(mocked_checksum, mock_contract):
    p = Payment(
        "random_account",
        "ronin:from_ronin",
        "ronin:from_private_ronin",
        "ronin:to_ronin",
        10)
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mock_contract.assert_called()
    assert p.contract == "contract"
    assert p.name == "random_account"
    assert p.from_acc == "0xfrom_ronin"
    assert p.from_private == "ronin:from_private_ronin"
    assert p.to_acc == "0xto_ronin"
    assert p.amount == 10


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_calls_web3_functions(mock_transaction_receipt,
                                      mock_contract,
                                      mock_keccak,
                                      mock_to_hex,
                                      mock_send,
                                      mock_sign,
                                      mock_checksum,
                                      _):
    p = Payment(
        "random_account",
        "ronin:from_ronin",
        "ronin:from_private_ronin",
        "ronin:to_ronin",
        10)
    p.execute()
    mock_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    assert mock_sign.call_args[1]['private_key'] == "ronin:from_private_ronin"
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("axie_utils.Payment.increase_gas_tx")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 0})
def test_execute_calls_web3_functions_retry(mock_transaction_receipt,
                                            mock_contract,
                                            mock_keccak,
                                            mock_to_hex,
                                            mock_send,
                                            mock_sign,
                                            mock_checksum,
                                            mock_increase_gas_tx,
                                            _):
    p = Payment(
        "random_account",
        "ronin:from_ronin",
        "ronin:from_private_ronin",
        "ronin:to_ronin",
        10)
    p.execute()
    mock_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    assert mock_sign.call_args[1]['private_key'] == "ronin:from_private_ronin"
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    mock_increase_gas_tx.assert_called_with(123)


@patch("axie_utils.payments.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.payments.ethereum.sign_tx", return_value=(b'a', b'b', b'c'))
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_calls_web3_functions_trezor(mock_transaction_receipt,
                                             mock_contract,
                                             mock_keccak,
                                             mock_to_hex,
                                             mock_send,
                                             mock_sign,
                                             mock_checksum,
                                             _,
                                             mocked_to_bytes,
                                             mock_rlp):
    p = TrezorPayment(
        "random_account",
        "client",
        "m/44'/60'/0'/0/0",
        "ronin:from_ronin",
        "ronin:to_ronin",
        10)
    p.execute()
    mock_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    mocked_to_bytes.assert_called()
    mock_rlp.assert_called()
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")


@patch("axie_utils.payments.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.payments.ethereum.sign_tx", return_value=(b'a', b'b', b'c'))
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 0})
@patch("axie_utils.payments.TrezorPayment.increase_gas_tx")
def test_execute_calls_web3_functions_retry_trezor(mock_increase_gas_tx,
                                                   mock_transaction_receipt,
                                                   mock_contract,
                                                   mock_keccak,
                                                   mock_to_hex,
                                                   mock_send,
                                                   mock_sign,
                                                   mock_checksum,
                                                   _,
                                                   mocked_to_bytes,
                                                   mock_rlp):
    p = TrezorPayment(
        "random_account",
        "client",
        "m/44'/60'/0'/0/0",
        "ronin:from_ronin",
        "ronin:to_ronin",
        10)
    p.execute()
    mock_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    mocked_to_bytes.assert_called()
    mock_rlp.assert_called()
    mock_checksum.assert_has_calls(calls=[
        call(SLP_CONTRACT),
        call('0xfrom_ronin'),
        call('0xto_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    mock_increase_gas_tx.assert_called_with(123)
