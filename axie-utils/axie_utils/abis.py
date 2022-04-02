AXIE_ABI = [{
    'constant': False,
    'inputs': [{'internalType': 'address', 'name': '_from',
               'type': 'address'}, {'internalType': 'address',
               'name': '_to', 'type': 'address'},
               {'internalType': 'uint256', 'name': '_tokenId',
               'type': 'uint256'}],
    'name': 'safeTransferFrom',
    'outputs': [{'internalType': 'bool', 'name': '_success',
                'type': 'bool'}],
    'payable': False,
    'stateMutability': 'nonpayable',
    'type': 'function',
    }, {
    'constant': False,
    'inputs': [{'internalType': 'uint256', 'name': '_sireId',
               'type': 'uint256'}, {'internalType': 'uint256',
               'name': '_matronId', 'type': 'uint256'}],
    'name': 'breedAxies',
    'outputs': [{'internalType': 'bool', 'name': '_success',
                'type': 'bool'}],
    'payable': False,
    'stateMutability': 'nonpayable',
    'type': 'function',
    }, {
    'constant': True,
    'inputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
    'name': 'balanceOf',
    'outputs': [{'internalType': 'uint256', 'name': '',
                'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function',
    },{
    'constant': True,
    'inputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
    'name': 'ownerOf',
    'outputs': [{'internalType': 'address', 'name': '',
                'type': 'address'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function',
    }, {
    'constant': True,
    'inputs': [{'internalType': 'address', 'name': '_owner',
               'type': 'address'}, {'internalType': 'uint256',
               'name': '_index', 'type': 'uint256'}],
    'name': 'tokenOfOwnerByIndex',
    'outputs': [{'internalType': 'uint256', 'name': '',
                'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function',
    }]

SLP_ABI = [{
    'constant': False,
    'inputs': [{'internalType': 'address', 'name': '_owner',
               'type': 'address'}, {'internalType': 'uint256',
               'name': '_amount', 'type': 'uint256'},
               {'internalType': 'uint256', 'name': '_createdAt',
               'type': 'uint256'}, {'internalType': 'bytes',
               'name': '_signature', 'type': 'bytes'}],
    'name': 'checkpoint',
    'outputs': [{'internalType': 'uint256', 'name': '_balance',
                'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'nonpayable',
    'type': 'function',
    }, {
    'constant': True,
    'inputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
    'name': 'balanceOf',
    'outputs': [{'internalType': 'uint256', 'name': '',
                'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function',
    }, {
    'constant': False,
    'inputs': [{'internalType': 'address', 'name': '_to',
               'type': 'address'}, {'internalType': 'uint256',
               'name': '_value', 'type': 'uint256'}],
    'name': 'transfer',
    'outputs': [{'internalType': 'bool', 'name': '_success',
                'type': 'bool'}],
    'payable': False,
    'stateMutability': 'nonpayable',
    'type': 'function',
    }]

BALANCE_ABI = [{
    'constant': True,
    'inputs': [{'internalType': 'address', 'name': '', 'type': 'address'}],
    'name': 'balanceOf',
    'outputs': [{'internalType': 'uint256', 'name': '',
                'type': 'uint256'}],
    'payable': False,
    'stateMutability': 'view',
    'type': 'function',
    }]

APPROVE_ABI = [{
        'constant': False,
        'inputs': [
            {'name': '_spender', 'type':'address'},
            {'name': '_value', 'type': 'uint256'}],
        'name': 'approve',
        'outputs': [],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    },{
        'constant': True,
        'inputs': [
            {'name': '_owner', 'type':'address'},
            {'name': '_spender', 'type': 'address'}],
        'name': 'allowance',
        'outputs': [{'internalType': 'uint256', 'name': '', 'type': 'uint256'}],
        'payable': False,
        'stateMutability': 'view',
        'type': 'function'
    }]

SCATTER_ABI = [{
        'constant': False,
        'inputs': [
            {'name': 'token', 'type':'address'},
            {'name': 'recipients', 'type': 'address[]'},
            {'name': 'values', 'type': 'uint256[]'}],
        'name': 'disperseTokenSimple',
        'outputs': [],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    }, {
        'constant': False,
        'inputs': [{'name': 'token', 'type': 'address'},{'name': 'recipients', 'type': 'address[]'},{'name': 'values', 'type': 'uint256[]'}],
        'name': 'disperseToken',
        'outputs': [],
        'payable': False,
        'stateMutability': 'nonpayable',
        'type': 'function'
    }, {
        'constant': False,
        'inputs': [{'name': 'recipients', 'type': 'address[]'},{'name': 'values', 'type': 'uint256[]'}],
        'name': 'disperseEther',
        'outputs': [],
        'payable': True,
        'stateMutability': 'payable',
        'type': 'function'
    }]
