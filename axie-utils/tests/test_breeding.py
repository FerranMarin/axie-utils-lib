from mock import patch

from axie_utils import Breed, TrezorBreed
from axie_utils.abis import AXIE_ABI
from axie_utils.utils import AXIE_CONTRACT, RONIN_PROVIDER_FREE, USER_AGENT


def test_breed_init():
    acc = 'ronin:<accountfoo_address>' + "".join([str(x) for x in range(10)]*4)
    private_acc = '0x<accountfoo_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    b = Breed(sire_axie=123, matron_axie=456, address=acc, private_key=private_acc)
    assert b.sire_axie == 123
    assert b.matron_axie == 456
    assert b.private_key == private_acc
    assert b.address == acc.replace("ronin:", "0x")


@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("axie_utils.breeding.get_nonce", return_value=1)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_breed_execute(mocked_provider,
                       mocked_checksum,
                       mocked_contract,
                       mock_get_nonce,
                       mocked_sign_transaction,
                       mock_raw_send,
                       mock_receipt,
                       mock_keccak,
                       mock_to_hex):
    acc = 'ronin:<accountfoo_address>' + "".join([str(x) for x in range(10)]*4)
    private_acc = '0x<accountfoo_private_address>012345' + "".join([str(x) for x in range(10)]*3)
    b = Breed(sire_axie=123, matron_axie=456, address=acc, private_key=private_acc)
    b.execute()
    mock_get_nonce.assert_called_once()
    mocked_provider.assert_called_with(
        RONIN_PROVIDER_FREE,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(AXIE_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_sign_transaction.assert_called_once()
    mock_raw_send.assert_called_once()
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_receipt.assert_called_with("transaction_hash")


@patch("axie_utils.breeding.parse_path", return_value="parsed_path")
def test_trezorbreed_init(mock_parse):
    acc = 'ronin:<accountfoo_address>' + "".join([str(x) for x in range(10)]*4)
    b = TrezorBreed(sire_axie=123, matron_axie=456, address=acc, client='client', bip_path="m/44'/60'/0'/0/0")
    assert b.sire_axie == 123
    assert b.matron_axie == 456
    assert b.client == "client"
    assert b.address == acc.replace("ronin:", "0x")
    assert b.bip_path == "parsed_path"


@patch("axie_utils.breeding.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch('axie_utils.breeding.ethereum.sign_tx')
@patch("axie_utils.breeding.get_nonce", return_value=1)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_trezorbreed_execute(mocked_provider,
                             mocked_checksum,
                             mocked_contract,
                             mock_get_nonce,
                             mocked_sign_transaction,
                             mock_raw_send,
                             mock_receipt,
                             mock_keccak,
                             mock_to_hex,
                             mocked_to_bytes,
                             mock_rlp):
    acc = 'ronin:<accountfoo_address>' + "".join([str(x) for x in range(10)]*4)
    b = TrezorBreed(sire_axie=123, matron_axie=456, address=acc, client='client', bip_path="m/44'/60'/0'/0/0")
    b.execute()
    mocked_to_bytes.assert_called()
    mock_rlp.assert_called()
    mock_get_nonce.assert_called_once()
    mocked_provider.assert_called_with(
        RONIN_PROVIDER_FREE,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(AXIE_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=AXIE_ABI)
    mocked_sign_transaction.assert_called_once()
    mock_raw_send.assert_called_once()
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")
    mock_receipt.assert_called_with("transaction_hash")
