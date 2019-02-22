# -*- coding: utf-8 -*-
"""Implement BankStatementParser for MT940 IBAN ING files."""

import logging
import re
from odoo.addons.account_bank_statement_import_mt940_base.mt940 import (
    MT940, str2amount, get_subfields, handle_common_subfields)

_logger = logging.getLogger(__name__)


class MT940Parser(MT940):
    """Parser for Knab MT940 bank statement import files."""

    tag_61_regex = re.compile(
        r'(?P<date>\d{6})(?P<line_date>\d{0,4})'
        r'(?P<sign>[CD])(?P<amount>\d+,(\d{2})?)N(?P<type>.{3})'
        r'(?P<reference>\w{0,16})//(?P<knabid>\w{16})'
    )

    def __init__(self):
        """Initialize parser - override at least header_regex."""
        super(MT940Parser, self).__init__()
        self.header_lines = 0

    def handle_tag_61(self, data):
        """get transaction values"""
        super(MT940Parser, self).handle_tag_61(data)
        re_61 = self.tag_61_regex.match(data)
        if not re_61:
            raise ValueError("Cannot parse %s" % data)
        parsed_data = re_61.groupdict()
        self.current_transaction['amount'] = (
            str2amount(parsed_data['sign'], parsed_data['amount']))
        self.current_transaction['ref'] = parsed_data['reference']
        self.current_transaction['id'] = parsed_data['knabid']

    def handle_tag_86(self, data):
        """Parse 86 tag containing reference data."""
        if not self.current_transaction:
            return
        codewords = ['RTRN', 'BENM', 'ORDP',
                     'TRTP', 'NAME', 'IBAN', 'BBAN', 'BIC',
                     'CSID', 'BUSP', 'MARF', 'EREF',
                     'PREF', 'REMI', 'ID', 'PURP', 'ULTB', 'ULTD',
                     'CREF', 'IREF', 'CNTP', 'ULTC', 'EXCH', 'CHGS', 'TRTP']
        subfields = get_subfields(data, codewords)
        transaction = self.current_transaction
        # If we have no subfields, set message to whole of data passed:
        if not subfields:
            transaction.message = data
        else:
            handle_common_subfields(transaction, subfields)
        # Prevent handling tag 86 later for non transaction details:
        self.current_transaction = None
