import re
from hashlib import md5


class AbAddressUtility(object):
    """
    This class parses common forms of australian addresses. 

    For example, an address could have many forms:

        Unit 2 42 Example ST, STANMORE, NSW 2048

        2/42 EXAMPLE ST, STANMORE NSW 2048

        U2 42-44 EXAMPLE STEET, STANMORE, NSW 2048

        2/42 EXAMPLE STEET, STANMORE, NSW 2048
        
        2/42-44 Example Street, Stanmore, NSW 2048

    :param addr_string: address string to parse.

    >>> AbAddressUtility('U2 42-44 Example St, STANMORE, NSW 2048')
    <AbAddressUtility(addr_string='U2 42-44 Example St, STANMORE, NSW 2048')>

    This class can parse all forms above, and other common forms and 
    assemble different forms as needed.

    Most importantly, it provides a standardised address, this is useful
    when processing multiple data scources with different address forms.

    It can be used to standardise addresses, split addresses into parts, 
    or assemble parts into different forms of addresses.

    :ivar addr_string: The string originally passed to the instance on creation. 
                       e.g. 'Unit 2 42-44 Example St, STANMORE, NSW 2048'
    :ivar address_abbr: Full address but abbreviation of street type.
                        e.g. '2/42-44 EXAMPLE ST, STANMORE NSW 2048'
    :ivar std_address:  Standardised address.
                        e.g. '2/42 EXAMPLE ST, STANMORE NSW 2048'
    :ivar address:  User friendly full address.
                    e.g. '2/42-44 Example Street, Stanmore NSW 2048'
    :ivar parsed_addr:  Break address into parts and return a dict.
    :ivar prop_id: MD5 value for the standardised address.
    """

    def __init__(self, addr_string):

        self.addr_string = addr_string
        self._addr_string = addr_string.upper()
        self._addr_string = self._clean_address(self._addr_string)

        # Try to locat comma
        split_addr = self._addr_string.split(',')
        if len(split_addr) == 2:      # Try to parse with 1 comma
            street_part, locality_part = [i.strip() for i in split_addr]
            prop_name = False
        
        elif len(split_addr) == 3:    # Try to parse with 2 commas
            if re.match(r"(?P<state>(NSW|ACT|QLD|VIC|TAS|SA|NT|WA)){1}\s+(?P<post>(\d{1,4}){1})",
                        split_addr[-1].strip()):
                street_part, locality_part = split_addr[0].strip(
                ), ' '.join([i.strip() for i in split_addr[-2:]])
            else:
                prop_name, street_part, locality_part = [
                    i.strip() for i in split_addr]

        
        elif len(split_addr) == 1:    # Try to guess without comma
            guess = self._addr_string.split()
            if len(guess) == 6 or len(guess) == 7:
                street_part, locality_part = ' '.join(
                    guess[:3]), ' '.join(guess[3:])
            else:
                raise Exception('Not Valid Address Foramt')
        else:
            raise Exception('Not Valid Address Foramt')
        
        # Parse street part
        street_part_patterns = [
            r"(UNIT|LOT|SHOP|SUITE|U|ROOM)\s*(?P<flat_number>[A-Z]*\d+[A-Z]*)\s+(?P<number>[A-Z]*\d+[A-Z]*(-[A-Z]*\d*[A-Z]*)*\b)\s+(?P<street_name>[^,]*?)$",
            r"(?P<flat_number>\b[A-Z]*\d+[A-Z]*)/(?P<number>[A-Z]*\d+[A-Z]*(-\d*[A-Z]*)*\b)\s+(?P<street_name>[^,]*?)$",
            r"(?P<number>[A-Z]*\d+[A-Z]*(-[A-Z]*\d*[A-Z]*)*\b)\s+(?P<street_name>[^,]*?)$"
        ]
        street_part_dict = {}
        for pattern in street_part_patterns:
            searched = re.search(pattern, street_part)
            if searched:
                street_part_dict = searched.groupdict()
                break
        
        # Parse locality part
        locality_part_patterns = [
            r'((?P<locality>^[A-Z]+((\s|-)*[A-Z]*)*)\s+(?P<state>(NSW|ACT|QLD|VIC|TAS|SA|NT|WA)){1}\s+(?P<post>(\d{1,4}){1}))',
            r'((?P<locality>^[A-Z]+((\s|-)*[A-Z]*)*)\s+(?P<state>(NSW|ACT|QLD|VIC|TAS|SA|NT|WA)){1})',
            r'((?P<locality>^[A-Z]+((\s|-)*[A-Z]*)*)\s+(?P<post>(\d{1,4}){1}))',
            r'(?P<locality>^[A-Z]+((\s|-)*[A-Z]*)*)'
        ]
        locality_part_dict = {}
        for pattern in locality_part_patterns:
            searched = re.search(pattern, locality_part)
            if searched:
                locality_part_dict = searched.groupdict()
                break
        
        # Parse flat number
        flat_number_part = street_part_dict.get('flat_number', None)
        if flat_number_part:
            flat_number_dict = re.search(
                r"(?P<flat_number_prefix>\b[A-Z]*)(?P<flat_number>\d+)(?P<flat_number_suffix>[A-Z]*)", flat_number_part).groupdict()
        else:
            flat_number_dict = {
                'flat_number_prefix': '',
                'flat_number': '',
                'flat_number_suffix': '',
            }

        # Parse street number
        number = street_part_dict.get('number', None)
        number_dict = re.search(
            r"((?P<number_first_prefix>\b[A-Z]+))*(?P<number_first>\d+)((?P<number_first_suffix>[A-Z]+))*(-((?P<number_last_prefix>\b[A-Z]+))*(?P<number_last>\d+)((?P<number_last_suffix>[A-Z]+))*)*", number).groupdict()
        for k, v in number_dict.items():
            if v is None:
                number_dict[k] = ''

        # Parse street name
        street_name_part = street_part_dict.get('street_name', None)
        street_name_dict = {
            'street_name': '',
            'street_type_abbr': '',
            'street_type': '',
            'street_suffix': '',
            'street_suffix_abbr': ''
        }
        street_name_list = street_name_part.split()

        # Deal with unofficial_abbrs
        street_name_list = self._deal_with_unofficial_abbrs(street_name_list)

        # Deal with street suffix
        street_name_list, street_name_dict = self._deal_street_suffix(street_name_list, street_name_dict)

        # Deal street abbr
        street_name_list, street_name_dict = self._deal_street_abbr(street_name_list, street_name_dict)

        # Assemble results
        self.parsed_addr = {}
        for d in (flat_number_dict, number_dict, street_name_dict, locality_part_dict):
            self.parsed_addr.update(d)

        a = self.parsed_addr
        self._flat = f"{a['flat_number_prefix']}{a['flat_number']}{a['flat_number_suffix']}"
        self._number_first = f"{a['number_first_prefix']}{a['number_first']}{a['number_first_suffix']}"
        self._number_last = f"{a['number_last_prefix']}{a['number_last']}{a['number_last_suffix']}"
        self._street_abbr = f"{a['street_name']}{' ' + a['street_type_abbr'] if len(a['street_type_abbr'])>0 else ''}{' '+a['street_suffix_abbr'] if len(a['street_suffix_abbr'])>0 else ''}"
        self._street = f"{a['street_name']}{' ' + a['street_type'] if len(a['street_type'])>0 else ''}{' '+a['street_suffix'] if len(a['street_suffix'])>0 else ''}"
        self._locality = a['locality']
        self._state = a['state']
        self._post = a['post']

        self.address_abbr = f"{self._flat+'/' if len(self._flat)>0 else ''}{self._number_first}{'-'+self._number_last if len(self._number_last)>0 else ''} {self._street_abbr}, {a['locality']} {a['state']} {a['post']}"

        # Generating id requires removal of last street_number
        self.std_address = f"{self._flat+'/' if len(self._flat)>0 else ''}{self._number_first} {self._street_abbr}, {a['locality']} {a['state']} {a['post']}"

        self.prop_id = md5(self.std_address.encode()).hexdigest()

        self.address = f"{self._flat+'/' if len(self._flat)>0 else ''}{self._number_first}{'-'+self._number_last if len(self._number_last)>0 else ''} {self._street.title()}, {a['locality'].title()} {a['state']} {a['post']}"

        for k, v in self.parsed_addr.items():
            if v == '':
                self.parsed_addr[k] = None

    @staticmethod
    def _clean_address(address):
        address = re.sub(r'"[A-Z\s]*"\s', '', address)
        address = re.sub(r"'[A-Z\s]*'\s", "", address)
        address = re.sub(r"\s{2,}", " ", address)
        address = re.sub(r",{2,}", ",", address)
        address = address.replace('"', '')
        address = address.replace('- ', '-')
        address = address.replace(' -', '-')
        address = address.replace('/ ', '/')
        address = address.replace(' /', '/')
        address = address.replace(' ,', ',')
        return address

    @classmethod
    def from_gnaf_dict(cls, **kwags):
        """Create an AbAddressUtility class from a dict containing GNAF
        information.

        :params **kwags: a dict from GNAF format.
        """
        a = {
            'flat_number_prefix': kwags.get('flat_number_prefix', None),
            'flat_number': kwags.get('flat_number', None),
            'flat_number_suffix': kwags.get('flat_number_suffix', None),
            'number_first_prefix': kwags.get('number_first_prefix', None),
            'number_first': kwags.get('number_first', None),
            'number_first_suffix': kwags.get('number_first_suffix', None),
            'number_last_prefix': kwags.get('number_last_prefix', None),
            'number_last': kwags.get('number_last', None),
            'number_last_suffix': kwags.get('number_last_suffix', None),
            'street_name': kwags.get('street_name', None),
            'street_type_code': kwags.get('street_type_code', None),
            'street_suffix_code': kwags.get('street_suffix_code', None),
            'locality_name': kwags.get('locality_name', None),
            'state_abbreviation': kwags.get('state_abbreviation', None),
            'postcode': kwags.get('postcode', None),
        }
        for k, v in a.items():
            if v is None:
                a[k] = ''
        _flat = f"{a['flat_number_prefix']}{a['flat_number']}{a['flat_number_suffix']}"
        _number_first = f"{a['number_first_prefix']}{a['number_first']}{a['number_first_suffix']}"
        _number_last = f"{a['number_last_prefix']}{a['number_last']}{a['number_last_suffix']}"
        _street = f"{a['street_name']} {a['street_type_code']}{' '+a['street_suffix_code']}"
        address = f"{_flat+'/' if len(_flat)>0 else ''}{_number_first}{'-'+_number_last if len(_number_last)>0 else ''} {_street.title()}, {a['locality_name'].title()} {a['state_abbreviation']} {a['postcode']}"
        return cls(address)

    @classmethod
    def from_elk_search(cls, **kwags):
        """Create an AbAddressUtility class from a dict containing ELK
        information.

        :params **kwags: a dict from ELK format.
        """
        a = {
            'flat_part': kwags.get('flat_part', None),
            'number_first': kwags.get('number_first', None),
            'number_last': kwags.get('number_last', None),
            'street_part': kwags.get('street_part', None),
            'locality': kwags.get('locality', None),
            'state': kwags.get('state', None),
        }
        for k, v in a.items():
            if v is None:
                a[k] = ''
        address = f"{a['flat_part']+'/' if len(a['flat_part'])>0 else ''}{a['number_first']}{('-'+a['number_last']) if len(a['number_last'])>0 else ''} {a['street_part']}, {a['locality']}, {a['state']}"
        return cls(address)

    def _deal_with_unofficial_abbrs(self, street_name_list):
        unofficial_abbrs = {'BLVD': 'BOULEVARD',
                            'LN': 'LANE', 'AV': 'AVENUE', "CR": "CRESCENT"}
        if street_name_list[-1] in unofficial_abbrs.keys():
            full_street_name = unofficial_abbrs[street_name_list[-1]]
            street_name_list = street_name_list[:-1] + [full_street_name]
        return street_name_list

    def _deal_street_suffix(self, street_name_list, street_name_dict):
        street_suffix_dict = {'WEST': 'W', 'EAST': 'E', 'NORTH': 'N', 'SOUTH': 'S', 'NORTHEAST': 'NE',
                              'SOUTHEAST': 'SE', 'NORTHWEST': 'NW', 'SOUTHWEST': 'SW'}
        if street_name_list[-1] in street_suffix_dict.keys():
            street_name_dict['street_suffix'] = street_name_list[-1]
            street_name_dict['street_suffix_abbr'] = street_suffix_dict[street_name_dict['street_suffix']]
            street_name_list = street_name_list[:-1]
        elif street_name_list[-1] in street_suffix_dict.values():
            street_name_dict['street_suffix_abbr'] = street_name_list[-1]
            for k, v in street_suffix_dict.items():
                if street_name_list[-1] == v:
                    street_name_dict['street_suffix'] = k
                    break
            street_name_list = street_name_list[:-1]
        return street_name_list, street_name_dict

    def _deal_street_abbr(self, street_name_list, street_name_dict):
        self.rd_abbr_dict = {'ACCESS': 'ACCS', 'ALLEY': 'ALLY', 'ALLEYWAY': 'ALWY', 'AMBLE': 'AMBL', 'APPROACH': 'APP',
                             'ARCADE': 'ARC', 'ARTERY': 'ART', 'ARTERIAL': 'ARTL', 'AVENUE': 'AVE', 'BANAN': 'BA',
                             'BROADWAY': 'BDWY', 'BEND': 'BEND', 'BRAE': 'BRAE', 'BRACE': 'BRCE', 'BREAK': 'BRK',
                             'BROW': 'BROW', 'BOULEVARD': 'BVD', 'BOARDWALK': 'BWLK', 'BYPASS': 'BYPA', 'BYWAY': 'BYWY',
                             'CAUSEWAY': 'CAUS', 'CIRCUIT': 'CCT', 'CUL': 'CDS', 'CHASE': 'CH', 'CIRCLE': 'CIR',
                             'CLOSE': 'CL', 'CIRCLET': 'CLT', 'COMMON': 'CMMN', 'CORNER': 'CNR', 'CONCOURSE': 'CON',
                             'COVE': 'COVE', 'COPSE': 'CPS', 'CIRCUS': 'CRCS', 'CRESCENT': 'CRES', 'CROSSING': 'CRSG',
                             'CROSS': 'CRSS', 'CREST': 'CRST', 'CUL-DE-SAC': 'CSAC', 'COURT': 'CT', 'CENTRE': 'CTR',
                             'COURTYARD': 'CTYD', 'CUTTING': 'CUTT', 'DALE': 'DALE', 'DEVIATION': 'DEVN', 'DIP': 'DIP',
                             'DRIVE': 'DR', 'DRIVEWAY': 'DRWY', 'DISTRIBUTOR': 'DSTR', 'EDGE': 'EDGE', 'ELBOW': 'ELB',
                             'END': 'END', 'ENTRANCE': 'ENT', 'ESPLANADE': 'ESP', 'EXPRESSWAY': 'EXP', 'EXTENSION': 'EXTN',
                             'FAIRWAY': 'FAWY', 'FIRETRAIL': 'FITR', 'FOLLOW': 'FOLW', 'FORMATION': 'FORM',
                             'FRONTAGE': 'FRTG', 'FIRETRACK': 'FTRK', 'FOOTWAY': 'FTWY', 'FREEWAY': 'FWY', 'GAP': 'GAP',
                             'GATE': 'GATE', 'GARDEN': 'GDN', 'GARDENS': 'GDNS', 'GLADE': 'GLD', 'GLEN': 'GLEN',
                             'GROVE': 'GR', 'GRANGE': 'GRA', 'GREEN': 'GRN', 'HILL': 'HILL', 'HIGHROAD': 'HRD',
                             'HEIGHTS': 'HTS', 'HIGHWAY': 'HWY', 'INTERCHANGE': 'INTG', 'JUNCTION': 'JNC', 'KEY': 'KEY',
                             'LANE': 'LANE', 'LINE': 'LINE', 'LINK': 'LINK', 'LOOKOUT': 'LKT', 'LANEWAY': 'LNWY',
                             'LOOP': 'LOOP', 'MALL': 'MALL', 'MEWS': 'MEWS', 'MEANDER': 'MNDR', 'MOTORWAY': 'MWY',
                             'NOOK': 'NOOK', 'OUTLOOK': 'OTLK', 'PASS': 'PASS', 'PATH': 'PATH', 'PARADE': 'PDE',
                             'PATHWAY': 'PHWY', 'PIAZZA': 'PIAZ', 'POCKET': 'PKT', 'PARKWAY': 'PKWY', 'PLACE': 'PL',
                             'PLAZA': 'PLZA', 'POINT': 'PNT', 'PORT': 'PORT', 'PROMENADE': 'PROM', 'PASSAGE': 'PSGE',
                             'QUADRANT': 'QDRT', 'QUAY': 'QY', 'QUAYS': 'QYS', 'RAMP': 'RAMP', 'ROAD': 'RD',
                             'RIDGE': 'RDGE', 'ROADS': 'RDS', 'REST': 'REST', 'RING': 'RING', 'RISE': 'RISE',
                             'RAMBLE': 'RMBL', 'ROW': 'ROW', 'ROWE': 'ROWE', 'ROUTE': 'RTE', 'RETREAT': 'RTT',
                             'ROTARY': 'RTY', 'RUE': 'RUE', 'SUBWAY': 'SBWY', 'SHUNT': 'SHUN', 'SPUR': 'SPUR',
                             'SQUARE': 'SQ', 'STREET': 'ST', 'STEPS': 'STPS', 'STRIP': 'STRP', 'STAIRS': 'STRS',
                             'SERVICEWAY': 'SVWY', 'TARN': 'TARN', 'TERRACE': 'TCE', 'THOROUGHFARE': 'THOR',
                             'TOLLWAY': 'TLWY', 'TOP': 'TOP', 'TOR': 'TOR', 'TRACK': 'TRK', 'TRAIL': 'TRL', 'TURN': 'TURN',
                             'UNDERPASS': 'UPAS', 'VALE': 'VALE', 'VIADUCT': 'VIAD', 'VIEW': 'VIEW', 'VISTA': 'VSTA',
                             'WALK': 'WALK', 'WAY': 'WAY', 'WHARF': 'WHRF', 'WALKWAY': 'WKWY', 'WYND': 'WYND',
                             'OVAL': 'OVAL'}

        if street_name_list[-1] in self.rd_abbr_dict.keys():
            if street_name_list[0] == 'THE' and len(street_name_list) == 2:
                street_name_dict['street_type_abbr'] = street_name_list[-1]
            else:
                street_name_dict['street_type_abbr'] = self.rd_abbr_dict[street_name_list[-1]]

            street_name_dict['street_name'] = ' '.join(street_name_list[:-1])
            street_name_dict['street_type'] = street_name_list[-1]

        elif street_name_list[-1] in self.rd_abbr_dict.values():
            street_name_dict['street_name'] = ' '.join(street_name_list[:-1])
            street_name_dict['street_type_abbr'] = street_name_list[-1]
            for k, v in self.rd_abbr_dict.items():
                if street_name_dict['street_type_abbr'] == v:
                    street_name_dict['street_type'] = k
                    break
            else:
                street_name_dict['street_name'] = ' '.join(street_name_list)
        else:
            street_name_dict['street_name'] = ' '.join(street_name_list)

        return street_name_list, street_name_dict

    def __repr__(self):
        return f"<AbAddressUtility(addr_string='{self.addr_string}')>"

def standardise_address(address_string):
    try:
        addr_cls = AbAddressUtility(address_string)
        return addr_cls.std_address
    except:
        return None
