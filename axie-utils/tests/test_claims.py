import builtins
from datetime import datetime, timedelta

import pytest
from mock import patch, mock_open, call
import requests_mock
from hexbytes import HexBytes
from eth_account.messages import encode_defunct

from axie_utils import Claim, TrezorClaim
from axie_utils.abis import SLP_ABI
from axie_utils.utils import SLP_CONTRACT, RONIN_PROVIDER, USER_AGENT
from tests.utils import MockedSignedMsg


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_claim_init(mocked_provider, mocked_checksum, mocked_contract):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')):
        c = Claim(account="ronin:foo", private_key="bar", acc_name="test_acc", force=False)
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mocked_contract.assert_called()
    assert c.private_key == "bar"
    assert c.account == "0xfoo"
    assert c.acc_name == "test_acc"
    assert c.force == False


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_claim_init_force(mocked_provider, mocked_checksum, mocked_contract):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')):
        c = Claim(account="ronin:foo", private_key="bar", acc_name="test_acc", force=True)
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mocked_contract.assert_called()
    assert c.private_key == "bar"
    assert c.account == "0xfoo"
    assert c.acc_name == "test_acc"
    assert c.force == True


@patch("axie_utils.claims.check_balance", return_value=10)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_slp(mocked_provider, mocked_checksum, mocked_contract, mocked_check):
    last_claimed_date = datetime.utcnow() - timedelta(days=15)
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       json={"total": 12,
                             "last_claimed_item_at": last_claimed_date.timestamp(),
                             "claimable_total": 0})
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='{"foo": "bar"}')):
            c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed == 2
        mocked_check.assert_called_with("0xfoo")
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_contract.assert_called()


@patch("axie_utils.claims.check_balance", return_value=10)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_failed_date(mocked_provider, mocked_checksum, mocked_contract, mocked_check):
    last_claimed_date = datetime.utcnow() - timedelta(days=13) + timedelta(minutes=1)
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       json={"total": 12,
                             "last_claimed_item_at": last_claimed_date.timestamp(),
                             "claimable_total": 0})
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='{"foo": "bar"}')):
            c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed is None
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_check.assert_not_called()
        mocked_contract.assert_called()


@patch("axie_utils.claims.check_balance", return_value=10)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_date_force(mocked_provider, mocked_checksum, mocked_contract, mocked_check):
    last_claimed_date = datetime.utcnow() - timedelta(days=14) + timedelta(minutes=1)
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       json={"total": 12,
                             "last_claimed_item_at": last_claimed_date.timestamp(),
                             "claimable_total": 0})
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='{"foo": "bar"}')):
            c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=True)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed == 2
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_check.assert_called()
        mocked_contract.assert_called()


@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_slp_failed_req(mocked_provider, mocked_checksum, mocked_contract):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       status_code=500)
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='{"foo": "bar"}')):
            c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed is None
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_contract.assert_called()


def test_create_random_msg():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createRandomMessage": "random_msg"}})
        resp = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False).create_random_msg()
        assert resp == "random_msg"


def test_create_random_msg_fail_req():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        status_code=500)
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        random_msg = c.create_random_msg()
        assert random_msg is None


def test_create_random_msg_fail_no_data_req():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={})
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        random_msg = c.create_random_msg()
        assert random_msg is None


def test_create_random_msg_fail_wrong_data_req():
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"foo": "bar"}})
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        random_msg = c.create_random_msg()
        assert random_msg is None


@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.claims.Claim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_get_jwt(mocked_provider, mocked_checksum, mocked_random_msg, mock_sign_message, _):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createAccessTokenWithSignature": {"accessToken": "test-token"}}})
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        resp = c.get_jwt()
        assert resp == "test-token"
        expected_payload = {
             "operationName": "CreateAccessTokenWithSignature",
             "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
             },
             "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
             "{createAccessTokenWithSignature(input: $input) "
             "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mocked_random_msg.assert_called_once()
    mock_sign_message.assert_called_with(encode_defunct(text="random_msg"), private_key=c.private_key)


@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.claims.Claim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_get_jwt_fail_req(mocked_provider, mocked_checksum, mocked_random_msg, mock_sign_message, _):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        status_code=500)
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        jwt = c.get_jwt()
        assert jwt is None
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called_with(encode_defunct(text="random_msg"), private_key=c.private_key)
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload


@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.claims.Claim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_jwq_fail_req_content(mocked_provider, mocked_checksum, mocked_random_msg, mock_sign_message, _):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", json={"data": {}})
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        jwt = c.get_jwt()
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert jwt is None
        assert req_mocker.request_history[0].json() == expected_payload
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called_with(encode_defunct(text="random_msg"), private_key=c.private_key)


@patch("web3.eth.Eth.contract")
@patch("web3.eth.Eth.account.sign_message", return_value={"signature": HexBytes(b"123")})
@patch("axie_utils.claims.Claim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_jwq_fail_req_content_2(mocked_provider, mocked_checksum, mocked_random_msg, mock_sign_message, _):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createAccessTokenWithSignature": {}}})
        c = Claim(account="ronin:foo", private_key="0xbar", acc_name="test_acc", force=False)
        jwt = c.get_jwt()
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload
        assert jwt is None
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called_with(encode_defunct(text="random_msg"), private_key=c.private_key)


@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.Claim.get_jwt", return_value="token")
@patch("axie_utils.claims.Claim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_claim_execution(mocked_provider,
                               mocked_checksum,
                               mocked_contract,
                               moocked_check_balance,
                               mocked_unclaimed_slp,
                               mock_get_jwt,
                               mock_get_nonce,
                               mocked_sign_transaction,
                               mock_raw_send,
                               mock_receipt,
                               mock_keccak,
                               mock_to_hex):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "456",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "signature": "0xsignature"
                        }
                    }
                }
            )
            c = Claim(account="ronin:foo", private_key="0x00003A01C01173D676B64123", acc_name="test_acc", force=False)
            c.execute()
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_has_calls([call(SLP_CONTRACT), call("0xfoo")])
    mocked_contract.assert_called()
    moocked_check_balance.assert_called_with("0xfoo")
    mocked_unclaimed_slp.assert_called_once()
    assert c.private_key == "0x00003a01c01173d676b64123"
    assert c.account == "0xfoo"
    mock_get_jwt.assert_called_once()
    mock_get_nonce.assert_called_with("0xfoo")
    mocked_sign_transaction.assert_called_once()
    mock_raw_send.assert_called_once()
    mock_receipt.assert_called_with("transaction_hash")
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")


@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("web3.eth.Eth.account.sign_transaction")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.Claim.get_jwt", return_value="token")
@patch("axie_utils.claims.Claim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_execution_failed_get_blockchain(mocked_provider,
                                               mocked_checksum,
                                               mocked_contract,
                                               moocked_check_balance,
                                               mocked_unclaimed_slp,
                                               mock_get_jwt,
                                               mock_get_nonce,
                                               mocked_sign_transaction,
                                               mock_raw_send,
                                               mock_receipt,
                                               mock_keccak,
                                               mock_to_hex):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='{"foo": "bar"}')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "",
                            "timestamp": 0,
                            "signature": ""
                        }
                    }
                }
            )
            c = Claim(account="ronin:foo", private_key="0x00003A01C01173D676B64123", acc_name="test_acc", force=False)
            c.execute()
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with('0xa8754b9fa15fc18bb59458815510e40a12cd2014')
        mocked_contract.assert_called()
        moocked_check_balance.assert_not_called()
        mocked_unclaimed_slp.assert_called_once()
        assert c.private_key == "0x00003a01c01173d676b64123"
        assert c.account == "0xfoo"
        mock_get_jwt.assert_called_once()
        mock_get_nonce.assert_not_called()
        mocked_sign_transaction.assert_not_called()
        mock_raw_send.assert_not_called()
        mock_receipt.assert_not_called()
        mock_keccak.assert_not_called()
        mock_to_hex.assert_not_called()


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_trezor_claim_init(mocked_provider, mocked_checksum, mocked_contract, mocked_parse):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='SLP_ABI')):
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
    assert c.bip_path == "parsed_path"
    assert c.client == "client"
    assert c.account == "0xfoo"
    assert c.acc_name == "test_acc"


@patch("axie_utils.claims.check_balance", return_value=10)
@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_slp_trezor(mocked_provider, mocked_checksum, mocked_contract, mocked_parse, mocked_check):
    last_claimed_date = datetime.now() - timedelta(days=15)
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       json={"total": 12,
                             "last_claimed_item_at": round(last_claimed_date.timestamp()),
                             "claimable_total": 0})
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='SLP_ABI')):
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed == 2
        mocked_check.assert_called_with("0xfoo")
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_has_unclaimed_slp_failed_req_trezor(mocked_provider, mocked_checksum, mocked_contract, mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.get("https://game-api.skymavis.com/game-api/clients/0xfoo/items/1",
                       status_code=500)
        with patch.object(builtins,
                          "open",
                          mock_open(read_data='SLP_ABI')):
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            unclaimed = c.has_unclaimed_slp()
            assert unclaimed is None
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_contract.assert_called()


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
def test_create_random_msg_trezor(mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createRandomMessage": "random_msg"}})
        r = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        resp = r.create_random_msg()
        assert resp == "random_msg"
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
def test_create_random_msg_fail_req_trezor(mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        status_code=500)
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        random_msg = c.create_random_msg()
        assert random_msg is None
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("axie_utils.claims.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.claims.TrezorClaim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_get_jwt_trezor(mocked_provider, mocked_checksum, mocked_random_msg, mock_sign_message, _, mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createAccessTokenWithSignature": {"accessToken": "test-token"}}})
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        resp = c.get_jwt()
        assert resp == "test-token"
        expected_payload = {
             "operationName": "CreateAccessTokenWithSignature",
             "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
             },
             "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
             "{createAccessTokenWithSignature(input: $input) "
             "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_checksum.assert_called_with(SLP_CONTRACT)
    mocked_random_msg.assert_called_once()
    mock_sign_message.assert_called()


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("axie_utils.claims.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.claims.TrezorClaim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_get_jwt_fail_req_trezor(
                                 mocked_provider,
                                 mocked_checksum,
                                 mocked_random_msg,
                                 mock_sign_message,
                                 _,
                                 mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        status_code=500)
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        jwt = c.get_jwt()
        assert jwt is None
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called()
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("axie_utils.claims.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.claims.TrezorClaim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_jwq_fail_req_content_trezor(
                                     mocked_provider,
                                     mocked_checksum,
                                     mocked_random_msg,
                                     mock_sign_message,
                                     _,
                                     mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql", json={"data": {}})
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        jwt = c.get_jwt()
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert jwt is None
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        assert req_mocker.request_history[0].json() == expected_payload
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called()


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("web3.eth.Eth.contract")
@patch("axie_utils.claims.ethereum.sign_message", return_value=MockedSignedMsg())
@patch("axie_utils.claims.TrezorClaim.create_random_msg", return_value="random_msg")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_jwq_fail_req_content_2_trezor(
                                        mocked_provider,
                                        mocked_checksum,
                                        mocked_random_msg,
                                        mock_sign_message,
                                        _,
                                        mocked_parse):
    with requests_mock.Mocker() as req_mocker:
        req_mocker.post("https://graphql-gateway.axieinfinity.com/graphql",
                        json={"data": {"createAccessTokenWithSignature": {}}})
        c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
        jwt = c.get_jwt()
        expected_payload = {
            "operationName": "CreateAccessTokenWithSignature",
            "variables": {
                "input": {
                    "mainnet": "ronin",
                    "owner": "0xfoo",
                    "message": "random_msg",
                    "signature": f"{HexBytes(b'123').hex()}"
                }
            },
            "query": "mutation CreateAccessTokenWithSignature($input: SignatureInput!)"
            "{createAccessTokenWithSignature(input: $input) "
            "{newAccount result accessToken __typename}}"
        }
        assert req_mocker.request_history[0].json() == expected_payload
        assert jwt is None
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with(SLP_CONTRACT)
        mocked_random_msg.assert_called_once()
        mock_sign_message.assert_called()


@pytest.mark.asyncio
@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("axie_utils.claims.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("axie_utils.claims.ethereum.sign_tx")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.TrezorClaim.get_jwt", return_value="token")
@patch("axie_utils.claims.TrezorClaim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
async def test_claim_async_execute_trezor(mocked_provider,
                                          mocked_checksum,
                                          mocked_contract,
                                          moocked_check_balance,
                                          mocked_unclaimed_slp,
                                          mock_get_jwt,
                                          mock_get_nonce,
                                          mocked_sign_transaction,
                                          mock_raw_send,
                                          mock_receipt,
                                          mock_keccak,
                                          mock_to_hex,
                                          mocked_to_bytes,
                                          mock_rlp,
                                          mocked_parse):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='SLP_ABI')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "456",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "signature": "0xsignature"
                        }
                    }
                }
            )
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            await c.async_execute()
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_to_bytes.assert_called()
    mock_rlp.assert_called()
    mocked_checksum.assert_has_calls([call(SLP_CONTRACT), call("0xfoo")])
    mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    moocked_check_balance.assert_called_with("0xfoo")
    mocked_unclaimed_slp.assert_called_once()
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
    assert c.bip_path == "parsed_path"
    assert c.client == "client"
    assert c.account == "0xfoo"
    mock_get_jwt.assert_called_once()
    mock_get_nonce.assert_called_with("0xfoo")
    mocked_sign_transaction.assert_called_once()
    mock_raw_send.assert_called_once()
    mock_receipt.assert_called_with("transaction_hash")
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")


@pytest.mark.asyncio
@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("axie_utils.claims.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("axie_utils.claims.ethereum.sign_tx")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.TrezorClaim.get_jwt", return_value="token")
@patch("axie_utils.claims.TrezorClaim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
async def test_async_execute_failed_get_blockchain_trezor(mocked_provider,
                                                          mocked_checksum,
                                                          mocked_contract,
                                                          moocked_check_balance,
                                                          mocked_unclaimed_slp,
                                                          mock_get_jwt,
                                                          mock_get_nonce,
                                                          mocked_sign_transaction,
                                                          mock_raw_send,
                                                          mock_receipt,
                                                          mock_keccak,
                                                          mock_to_hex,
                                                          mocked_to_bytes,
                                                          mock_rlp,
                                                          mocked_parse):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='SLP_ABI')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "",
                            "timestamp": 0,
                            "signature": ""
                        }
                    }
                }
            )
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            await c.async_execute()
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with('0xa8754b9fa15fc18bb59458815510e40a12cd2014')
        mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)
        moocked_check_balance.assert_not_called()
        mocked_unclaimed_slp.assert_called_once()
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        assert c.bip_path == "parsed_path"
        assert c.client == "client"
        assert c.account == "0xfoo"
        mock_get_jwt.assert_called_once()
        mock_get_nonce.assert_not_called()
        mocked_sign_transaction.assert_not_called()
        mock_raw_send.assert_not_called()
        mock_receipt.assert_not_called()
        mock_keccak.assert_not_called()
        mock_to_hex.assert_not_called()
        mock_rlp.assert_not_called()
        mocked_to_bytes.assert_not_called()


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("axie_utils.claims.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("axie_utils.claims.ethereum.sign_tx")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.TrezorClaim.get_jwt", return_value="token")
@patch("axie_utils.claims.TrezorClaim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_claim_execute_trezor(mocked_provider,
                              mocked_checksum,
                              mocked_contract,
                              moocked_check_balance,
                              mocked_unclaimed_slp,
                              mock_get_jwt,
                              mock_get_nonce,
                              mocked_sign_transaction,
                              mock_raw_send,
                              mock_receipt,
                              mock_keccak,
                              mock_to_hex,
                              mocked_to_bytes,
                              mock_rlp,
                              mocked_parse):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='SLP_ABI')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "456",
                            "timestamp": str(int(datetime.now().timestamp())),
                            "signature": "0xsignature"
                        }
                    }
                }
            )
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            c.execute()
    mocked_provider.assert_called_with(
        RONIN_PROVIDER,
        request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
    )
    mocked_to_bytes.assert_called()
    mock_rlp.assert_called()
    mocked_checksum.assert_has_calls([call(SLP_CONTRACT), call("0xfoo")])
    mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)
    moocked_check_balance.assert_called_with("0xfoo")
    mocked_unclaimed_slp.assert_called_once()
    mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
    assert c.bip_path == "parsed_path"
    assert c.client == "client"
    assert c.account == "0xfoo"
    mock_get_jwt.assert_called_once()
    mock_get_nonce.assert_called_with("0xfoo")
    mocked_sign_transaction.assert_called_once()
    mock_raw_send.assert_called_once()
    mock_receipt.assert_called_with("transaction_hash")
    mock_keccak.assert_called_once()
    mock_to_hex.assert_called_with("result_of_keccak")


@patch("axie_utils.graphql.parse_path", return_value="parsed_path")
@patch("axie_utils.claims.rlp.encode")
@patch("web3.Web3.toBytes")
@patch("web3.Web3.toHex", return_value="transaction_hash")
@patch("web3.Web3.keccak", return_value='result_of_keccak')
@patch("web3.eth.Eth.get_transaction_receipt", return_value={'status': 1})
@patch("web3.eth.Eth.send_raw_transaction", return_value="raw_tx")
@patch("axie_utils.claims.ethereum.sign_tx")
@patch("axie_utils.claims.get_nonce", return_value=1)
@patch("axie_utils.claims.TrezorClaim.get_jwt", return_value="token")
@patch("axie_utils.claims.TrezorClaim.has_unclaimed_slp", return_value=456)
@patch("axie_utils.claims.check_balance", return_value=123)
@patch("web3.eth.Eth.contract")
@patch("web3.Web3.toChecksumAddress", return_value="checksum")
@patch("web3.Web3.HTTPProvider", return_value="provider")
def test_execute_failed_get_blockchain_trezor(mocked_provider,
                                              mocked_checksum,
                                              mocked_contract,
                                              moocked_check_balance,
                                              mocked_unclaimed_slp,
                                              mock_get_jwt,
                                              mock_get_nonce,
                                              mocked_sign_transaction,
                                              mock_raw_send,
                                              mock_receipt,
                                              mock_keccak,
                                              mock_to_hex,
                                              mocked_to_bytes,
                                              mock_rlp,
                                              mocked_parse):
    with patch.object(builtins,
                      "open",
                      mock_open(read_data='SLP_ABI')):
        with requests_mock.Mocker() as req_mocker:
            req_mocker.post(
                "https://game-api.skymavis.com/game-api/clients/0xfoo/items/1/claim",
                json={
                    "blockchain_related": {
                        "signature": {
                            "amount": "",
                            "timestamp": 0,
                            "signature": ""
                        }
                    }
                }
            )
            c = TrezorClaim(account="ronin:foo", acc_name="test_acc", bip_path="m/44'/60'/0'/0/0", client="client", force=False)
            c.execute()
        mocked_provider.assert_called_with(
            RONIN_PROVIDER,
            request_kwargs={"headers": {"content-type": "application/json", "user-agent": USER_AGENT}}
        )
        mocked_checksum.assert_called_with('0xa8754b9fa15fc18bb59458815510e40a12cd2014')
        mocked_contract.assert_called_with(address="checksum", abi=SLP_ABI)
        moocked_check_balance.assert_not_called()
        mocked_unclaimed_slp.assert_called_once()
        mocked_parse.assert_called_with("m/44'/60'/0'/0/0")
        assert c.bip_path == "parsed_path"
        assert c.client == "client"
        assert c.account == "0xfoo"
        mock_get_jwt.assert_called_once()
        mock_get_nonce.assert_not_called()
        mocked_sign_transaction.assert_not_called()
        mock_raw_send.assert_not_called()
        mock_receipt.assert_not_called()
        mock_keccak.assert_not_called()
        mock_to_hex.assert_not_called()
        mock_rlp.assert_not_called()
        mocked_to_bytes.assert_not_called()