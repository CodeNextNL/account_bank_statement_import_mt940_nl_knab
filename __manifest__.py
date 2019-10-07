# Copyright (C) codeNext
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Import Knab T940 Bank Statements',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'codeNext, '
              'Odoo Community Association (OCA)',
    'website': 'https://www.codenext.nl',
    'category': 'Banking addons',
    'depends': [
        'account_bank_statement_import_mt940_base'
    ],
    'data': [
        'views/account_bank_statement_import.xml',
    ],
    'installable': True,
}
