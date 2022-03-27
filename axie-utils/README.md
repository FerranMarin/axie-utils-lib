# Axie Utils Library

Aim of this library is to contain all the actions one might want to do when building tools around the Axie Infinity videogame. It started with me building an automation tool and needing to build different solutions. Extracting this functionality allows for that easily.

**NOTE: Only v1 of this library uses free tx, from v2 and onwards all transactions consume RON. That is due to now free tx being much more rare to have available.**


# Installation

Install and update using pip:

```
pip install -U axie-utils
```

# Simple Example

This example would send 100 SLP from `ronin:from_where_to_send_SLP` to `ronin:to_where_we_send_SLP`.

``` python
from axie_utils import Payment

p = Payment(
    "Testing Account",
    "ronin:from_where_to_send_SLP",
    "0x:private_key_from_the_from_acc",
    "ronin:to_where_we_send_SLP",
    100)

p.execute()
```

This example, shows how we would claim SLP from an account.

``` python
from axie_utils import Claim

c = Claim(
    "Testing Account",
    "ronin:acc_to_claim",
    "0x:private_key_from_acc_to_claim"
)
c.execute()

```

# Documentation

For furhter documentation, please visit this [link](https://ferranmarin.github.io/axie-utils-lib/).
