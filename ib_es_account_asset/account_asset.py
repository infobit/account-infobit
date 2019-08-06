# -*- encoding: utf-8 -*-
import calendar
from datetime import datetime
from openerp import fields, models, api
#from openerp.osv import orm, fields
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF

class account_asset_asset(models.Model):
    _inherit = 'account.asset.asset'

    def _calc_date_end(self):
        res={}
        for data in self:
           if data.depreciation_line_ids:
              res[data.id] = str(data.depreciation_line_ids[(len(data.depreciation_line_ids)-1)].depreciation_date)
        return res

    aa_logic = fields.Float('A.A. Logic', digits=(3, 2))
    valor_compra = fields.Float('Valor de Compra', digits=(3, 2))
    fecha_compra = fields.Date('Fecha de Compra')
    fecha_venta = fields.Date('Fecha de Venta')
    importe_venta = fields.Float('Importe Venta', digits=(3, 2))
    account_id = fields.Char(string='Cuenta Contable', related='category_id.account_asset_id.code', store=True)
    date_end = fields.Date(compute='_calc_date_end', string='Fecha Fin Amortización', store=True)
