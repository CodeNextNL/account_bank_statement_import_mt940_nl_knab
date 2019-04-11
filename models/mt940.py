# -*- coding: utf-8 -*-

# Copyright (C) codeNext
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

"""Implement BankStatementParser for MT940 Knab files."""

import re
from odoo.addons.account_bank_statement_import_mt940_base.mt940 import (
    MT940, str2amount, get_subfields)


def get_counterpart(transaction, subfield):
    """Get counterpart from transaction.

    Counterpart is often stored in subfield of tag 86. The subfield
    can be IBAN, BBAN, BIC, NAME"""
    if not subfield:
        return  # subfield is empty
    if len(subfield) >= 1 and subfield[0]:
        transaction.update({'account_number': subfield[0]})
    if len(subfield) >= 1 and subfield[1]:
        transaction.update({'account_number': subfield[1]})
    if len(subfield) >= 1 and subfield[2]:
        transaction.update({'account_bic': subfield[2]})
    if len(subfield) >= 1 and subfield[3]:
        transaction.update({'partner_name': subfield[3]})


def handle_common_subfields(transaction, subfields):
    """Deal with common functionality for tag 86 subfields."""
    # Get counterpart from IBAN, BIC or NAME subfields:
    counterpart_fields = []
    for counterpart_field in ['IBAN', 'BBAN', 'BIC', 'NAME']:
        if counterpart_field in subfields:
            new_value = subfields[counterpart_field][0].replace('CUI/CNP', '')
            counterpart_fields.append(new_value)
        else:
            counterpart_fields.append('')
    if counterpart_fields:
        get_counterpart(transaction, counterpart_fields)
    if not transaction.get('name'):
        transaction['name'] = ''
    # REMI: Remitter information (text entered by other party on trans.):
    if 'REMI' in subfields:
        transaction['name'] += (
            subfields['REMI'][2]
            # this might look like
            # /REMI/USTD//<remittance info>/
            # or
            # /REMI/STRD/CUR/<betalingskenmerk>/
            if len(subfields['REMI']) >= 3 and subfields['REMI'][0] in [
                'STRD', 'USTD'
            ]
            else
            '/'.join(x for x in subfields['REMI'] if x)
        )
    # EREF: End-to-end reference
    if 'EREF' in subfields:
        transaction['name'] += '/'.join(filter(bool, subfields['EREF']))
    # Get transaction reference subfield (might vary):
    if transaction.get('ref') in subfields:
        transaction['ref'] = ''.join(subfields[transaction['ref']])


class MT940Parser(MT940):
    """Parser for Knab MT940 bank statement import files."""

    tag_61_regex = re.compile(
        r'(?P<date>\d{6})(?P<line_date>\d{0,4})'
        r'(?P<sign>[CD])(?P<amount>\d+,(\d{1,2})?)N(?P<type>.{3})'
        r'(?P<reference>\w.{0,16})//(?P<knabid>\w{16})'
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
        self.current_transaction['note'] = parsed_data['reference']
        self.current_transaction['id'] = parsed_data['knabid']

    def handle_tag_86(self, data):
        """Parse 86 tag containing reference data."""
        if not self.current_transaction:
            return
        codewords = ['IBAN', 'BBAN', 'CNTN', 'BIC', 'NAME',
                     'CSID', 'MARF', 'EREF', 'RTRN', 'REMI']
        subfields = get_subfields(data, codewords)
        transaction = self.current_transaction
        # If we have no subfields, set message to whole of data passed:
        if not subfields:
            transaction.message = data
        else:
            handle_common_subfields(transaction, subfields)
        # Prevent handling tag 86 later for non transaction details:
        self.current_transaction = None
