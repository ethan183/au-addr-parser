from au_address_parser import AbAddressUtility

def test_pars_unit():
    address_cls = AbAddressUtility('Unit 2 42-44 Example ST, STANMORE,  NSW 2048')
    assert address_cls.address == '2/42-44 Example Street, Stanmore NSW 2048'
    assert address_cls.std_address == '2/42 EXAMPLE ST, STANMORE NSW 2048'
    assert address_cls.address_abbr == '2/42-44 EXAMPLE ST, STANMORE NSW 2048'
    assert address_cls.parsed_addr == {'flat_number_prefix': None,
                                        'flat_number': '2',
                                        'flat_number_suffix': None,
                                        'number_first_prefix': None,
                                        'number_first': '42',
                                        'number_first_suffix': None,
                                        'number_last_prefix': None,
                                        'number_last': '44',
                                        'number_last_suffix': None,
                                        'street_name': 'EXAMPLE',
                                        'street_type_abbr': 'ST',
                                        'street_type': 'STREET',
                                        'street_suffix': None,
                                        'street_suffix_abbr': None,
                                        'locality': 'STANMORE',
                                        'state': 'NSW',
                                        'post': '2048'}

def test_pars_house():
    address_cls = AbAddressUtility('22 Example ST, STANMORE, NSW 2048')
    assert address_cls.address == '22 Example Street, Stanmore NSW 2048'
    assert address_cls.std_address == '22 EXAMPLE ST, STANMORE NSW 2048'
    assert address_cls.address_abbr == '22 EXAMPLE ST, STANMORE NSW 2048'
    assert address_cls.parsed_addr == {'flat_number_prefix': None,
                                        'flat_number': None,
                                        'flat_number_suffix': None,
                                        'number_first_prefix': None,
                                        'number_first': '22',
                                        'number_first_suffix': None,
                                        'number_last_prefix': None,
                                        'number_last': None,
                                        'number_last_suffix': None,
                                        'street_name': 'EXAMPLE',
                                        'street_type_abbr': 'ST',
                                        'street_type': 'STREET',
                                        'street_suffix': None,
                                        'street_suffix_abbr': None,
                                        'locality': 'STANMORE',
                                        'state': 'NSW',
                                        'post': '2048'}

def test_pars_special():
    address_cls = AbAddressUtility('22 Example ST west, STANMORE, NSW 2048')
    assert address_cls.address == '22 Example Street West, Stanmore NSW 2048'
    assert address_cls.std_address == '22 EXAMPLE ST W, STANMORE NSW 2048'
    assert address_cls.address_abbr == '22 EXAMPLE ST W, STANMORE NSW 2048'
    assert address_cls.parsed_addr == {'flat_number_prefix': None,
                                        'flat_number': None,
                                        'flat_number_suffix': None,
                                        'number_first_prefix': None,
                                        'number_first': '22',
                                        'number_first_suffix': None,
                                        'number_last_prefix': None,
                                        'number_last': None,
                                        'number_last_suffix': None,
                                        'street_name': 'EXAMPLE',
                                        'street_type_abbr': 'ST',
                                        'street_type': 'STREET',
                                        'street_suffix': 'WEST',
                                        'street_suffix_abbr': 'W',
                                        'locality': 'STANMORE',
                                        'state': 'NSW',
                                        'post': '2048'}