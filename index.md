# Axie Utils Library

Aim of this library is to contain all the actions one might want to do when building tools around [Axie Infinity](https://axieinfinity.com/). All you should need if you build a Python tool is to use this library.
It does support trezor and non-trezor operations.

**Trezor Disclaimer**: _Current version supports Trezor One version 1.8.0 and up, and Trezor T version 2.1.0 and up._


# Installation

Install and update using pip:

```
pip install -U axie-utils
```

# Usage

## Non-Trezor

```python
from axie_utils import (
    Axies,
    AxieGraphQL,
    Breed,
    Claim,
    CustomUI,
    Morph,
    Payment,
    Transfer,
    get_nonce,
    check_balance)


# Transfer Axies
t = Transfer(
    from_acc="ronin:who_has_the_axie",
    from_private="0xprivate_key_from_acc",
    to_acc="ronin:where_to_send_the_axie",
    axie_id=123
)
t.execute()

# Breed Axies
b = Breed(
    sire_axie=123,
    matron_axie=456,
    address="ronin:where_the_axies_are",
    private_key="0xaddress_private_key"
)
b.execute()

# Payments
p = Payment(
    name='test_payment',
    from_acc="ronin:where_slp_is",
    from_private="0xaccount_where_slp_is_private_key",
    to_acc="ronin:where_to_send_slp",
    amount=1000
)
p.execute()

# Morphing
m = Morph(
    account="ronin:where_to_claim_slp",
    private_key="0xaccount_private_key",
    axie=123
)
m.execute()

# Claiming SLP
c = Claim(
    acc_name="Test Account",
    account="ronin:where_to_claim_slp",
    private_key="0xaccount_private_key"
)
c.execute()

# or asynchronously
 await c.async_execute()

# Get JWT

g = AxieGraphQL(
    account="ronin:where_to_claim_slp",
    private_key="0xaccount_private_key"
)
g.get_jwt()
g.create_random_msg()

# Utils

slp_balance = check_balance("ronin:to_check_the_balance")
slp_balance = check_balance("ronin:to_check_the_balance", 'slp')
axs_balance = check_balance("ronin:to_check_the_balance", 'axs')
axies_balance = check_balance("ronin:to_check_the_balance", 'axies')
weth_balance = check_balance("ronin:to_check_the_balance", 'weth')

nonce = get_nonce("ronin:to_check_its_nonce")
```

## Trezor

```python
from axie_utils import (
    CustomUI,
    TrezorAxieGraphQL,
    TrezorBreed,
    TrezorClaim,
    TrezorConfig,
    TrezorMorph,
    TrezorPayment,
    TrezorTransfer)
from trezorlib.client import get_default_client

client = get_default_client(
    # Passphrase can be empty ''. You can also not use the CustomUI, but it will ask the user for the passphrase later on
    ui=CustomUI(passphrase='passphrase'))

# Helper to find your bip paths
# resp will be a dictionary containing each address as a key and a dictionary with "bip_path" and "passphrase" as value
# In this example we simulate a trezor device that has 10 addreses with no passphrase

tc = TrezorConfig(10)
resp = tc.list_bip_paths()

# This example does have a passphrase and 50 addreses
other_tc = TrezorConfig(50, 'foo')
resp = tc.list_bip_paths()

# Transfer Axies
t = TrezorTransfer(
    from_acc="ronin:who_has_the_axie",
    client=client,
    bip_path="m/44'/60'/0'/0/0",
    to_acc="ronin:where_to_send_the_axie",
    axie_id=123
)
t.execute()

# Breed Axies
b = TrezorBreed(
    sire_axie=123,
    matron_axie=456,
    address="ronin:where_the_axies_are",
    client=client,
    bip_path="m/44'/60'/0'/0/0"
)
b.execute()

# Payments
p = TrezorPayment(
    name='test_payment',
    client=client,
    bip_path="m/44'/60'/0'/0/0",
    from_acc="ronin:where_slp_is",
    to_acc="ronin:where_to_send_slp",
    amount=1000
)
p.execute()

# Morphing
m = TrezorMorph(
    account="ronin:where_axie_to_morph_is",
    client=client,
    bip_path="m/44'/60'/0'/0/0"
    axie=123
)
m.execute()

# Claiming SLP
c = TrezorClaim(
    acc_name="Test Account",
    account="ronin:where_to_claim_slp",
    client=client,
    bip_path="m/44'/60'/0'/0/0"
)

c.execute()

# or asynchronously
 await c.async_execute()

# Get JWT

g = TrezorAxieGraphQL(
    account="ronin:where_to_claim_slp",
    client=client,
    bip_path="m/44'/60'/0'/0/0"
)
g.get_jwt()
g.create_random_msg()
```

Note: To create the QRCode scholars use to play, all you need to do is encode the JWT as a qrcode.
