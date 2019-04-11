# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import api, fields, models


class type_taxes_information(models.Model):
    _name = 'type.taxes.information'
    
    name = fields.Selection(selection=[
        ('outputtax', 'Output TAX'),
        ('inputtax', 'Input TAX'),
        ('inputtax_not_deductible', 'Input TAX not deductible'),
        ('tax_withholdings', 'Tax withholdings'),
        ('equivalence_surcharge', 'Equivalence surcharge')],
        string='Type')
    exclude = fields.Boolean('Exclude')
    type_tax_use = fields.Selection(selection=[
        ('sale', 'Sale'),
        ('purchase', 'Purchase'),
        ('none', 'None')],
        string='Type tax use')
