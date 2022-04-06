from mock import patch, call

from axie_utils.abis import AXIE_ABI
from axie_utils.transfers import Transfer, TrezorTransfer
from axie_utils.utils import AXIE_CONTRACT


@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_transfer(mock_transaction_receipt,
                          mock_contract,
                          mock_keccak,
                          mock_to_hex,
                          mock_send,
                          mock_sign,
                          mock_checksum,
                          mocked_get_transaction_count):
    t = Transfer(
        "ronin:from_ronin",
        "0xsecret",
        "ronin:to_ronin",
        123
    )
    t.execute()
    mock_contract.assert_called_with(address='checksum', abi=AXIE_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    assert mock_sign.call_args[1]['private_key'] == "0xsecret"
    mock_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT),
        call('0xfrom_ronin'),
        call('0xfrom_ronin'),
        call('0xto_ronin'),
        call('0xfrom_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    mocked_get_transaction_count.assert_called()


@patch("axie_utils.transfers.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.eth.Eth.get_transaction_count", return_value=123)
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("axie_utils.transfers.ethereum.sign_tx", return_value=(b'a', b'b', b'c'))
@patch("web3.eth.Eth.send_raw_transaction")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
def test_execute_transfer_trezor(mock_transaction_receipt,
                                 mock_contract,
                                 mock_keccak,
                                 mock_to_hex,
                                 mock_send,
                                 mock_sign,
                                 mock_checksum,
                                 mocked_get_transaction_count,
                                 mocked_to_bytes,
                                 mocked_rlp):
    t = TrezorTransfer(
        to_acc="ronin:to_ronin",
        client="client",
        bip_path="m/44'/60'/0'/0/0",
        from_acc="ronin:from_ronin",
        axie_id=123
    )
    t.execute()
    mock_contract.assert_called_with(address='checksum', abi=AXIE_ABI)
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_send.assert_called_once()
    mock_sign.assert_called_once()
    mocked_to_bytes.assert_called()
    mocked_rlp.assert_called()
    mock_checksum.assert_has_calls(calls=[
        call(AXIE_CONTRACT),
        call('0xfrom_ronin'),
        call('0xfrom_ronin'),
        call('0xto_ronin'),
        call('0xfrom_ronin')])
    mock_transaction_receipt.assert_called_with("transaction_hash")
    mocked_get_transaction_count.assert_called()
