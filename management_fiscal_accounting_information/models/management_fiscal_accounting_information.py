# -*- coding: utf-8 -*-
# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 Eficent Business and IT Consulting Services, S.L.
#                <contact@eficent.com>
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
from odoo import models, api, fields, _
from odoo.exceptions import Warning as UserError
import re
from calendar import monthrange
from odoo.tools import config
from datetime import datetime

class ManagementFiscalAccountingInformation(models.Model):
    _name = 'management.fiscal.accounting.information'
    _period_yearly = True
    _period_quarterly = True
    _period_monthly = True

    def _default_company_id(self):
        company_obj = self.env['res.company']
        return company_obj._company_default_get('l10n.es.aeat.report')

    def _default_journal(self):
        return self.env['account.journal'].search(
            [('type', '=', 'general')])[:1]

    def get_period_type_selection(self):
        period_types = []
        if self._period_yearly or config['test_enable']:
            period_types += [('0A', '0A - Anual')]
        if self._period_quarterly:
            period_types += [('1T', '1T - Primer trimestre'),
                             ('2T', '2T - Segundo trimestre'),
                             ('3T', '3T - Tercer trimestre'),
                             ('4T', '4T - Cuarto trimestre')]
        if self._period_monthly or config['test_enable']:
            period_types += [('01', '01 - Enero'),
                             ('02', '02 - Febrero'),
                             ('03', '03 - Marzo'),
                             ('04', '04 - Abril'),
                             ('05', '05 - Mayo'),
                             ('06', '06 - Junio'),
                             ('07', '07 - Julio'),
                             ('08', '08 - Agosto'),
                             ('09', '09 - Septiembre'),
                             ('10', '10 - Octubre'),
                             ('11', '11 - Noviembre'),
                             ('12', '12 - Diciembre')]
        return period_types

    def _default_period_type(self):
        selection = self.get_period_type_selection()
        return selection and selection[0][0] or False

    def _default_year(self):
        return fields.Date.from_string(fields.Date.today()).year


    company_id = fields.Many2one(
        comodel_name='res.company', string="Company", required=True,
        readonly=True, default=_default_company_id,
        states={'draft': [('readonly', False)]})
    year = fields.Integer(string="Year", default=_default_year, required=True, readonly=True, states={'draft': [('readonly', False)]})
    calculation_date = fields.Datetime(string="Calculation date")
    name = fields.Char(string="Report identifier", size=13, oldname='sequence')
    period_type = fields.Selection(
        selection='get_period_type_selection', string="Period type",
        required=True, default=_default_period_type,
        readonly=True, states={'draft': [('readonly', False)]})
    date_start = fields.Date(
        string="Starting date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    date_end = fields.Date(
        string="Ending date", required=True, readonly=True,
        states={'draft': [('readonly', False)]})
    journal_ids = fields.Many2many('account.journal', 'journal_rel_information', 'journal_rel_id', 'journal_id', string="Journals")
    tax_ids = fields.Many2many('account.tax', 'tax_rel_information', 'tax_rel_id', 'tax_id', string="Taxes", required=True)
    partner_ids = fields.Many2many('res.partner', 'partner_rel_information', 'partner_rel_id', 'partner_id', string="Partners", required=True)
    estructure_tax_line_ids = fields.One2many('estructure.tax.line', 'management_id', 'Lines of Taxes')
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('calculated', 'Processed'),
            ('done', 'Done'),
            ('posted', 'Posted'),
            ('cancelled', 'Cancelled'),
        ], string='State', default='draft', readonly=True)

    """_sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'AEAT report identifier must be unique'),
    ]"""

    @api.onchange('year', 'period_type')
    def onchange_period_type(self):
        if not self.year or not self.period_type:
            self.date_start = False
            self.date_end = False
        else:
            if self.period_type == '0A':
                # Anual
                self.date_start = fields.Date.from_string(
                    '%s-01-01' % self.year)
                self.date_end = fields.Date.from_string(
                    '%s-12-31' % self.year)
            elif self.period_type in ('1T', '2T', '3T', '4T'):
                # Trimestral
                starting_month = 1 + (int(self.period_type[0]) - 1) * 3
                ending_month = starting_month + 2
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, starting_month))
                self.date_end = fields.Date.from_string(
                    '%s-%s-%s' % (
                        self.year, ending_month,
                        monthrange(self.year, ending_month)[1]))
            elif self.period_type in ('01', '02', '03', '04', '05', '06',
                                      '07', '08', '09', '10', '11', '12'):
                # Mensual
                month = int(self.period_type)
                self.date_start = fields.Date.from_string(
                    '%s-%s-01' % (self.year, month))
                self.date_end = fields.Date.from_string('%s-%s-%s' % (
                    self.year, month, monthrange(self.year, month)[1]))
            #self.export_config_id = self._get_export_config(self.date_start).id

    def calculate_taxes_summary(self):
      if self.state == 'draft':
        if self.tax_ids:
         for rec in self:
           tax_model = self.env['account.tax']
           taxes = [x.id for x in self.tax_ids]
           journals = [x.id for x in self.journal_ids]
           partners = [x.id for x in self.partner_ids]
           """self._cr.execute("SELECT  a.parent_id as cuenta, ap.code as code, ap.name as descripcion, sum(t.tax_amount) as cuota, " + "sum(t.base_amount) as base FROM account_invoice_tax t inner join account_invoice ic on t.invoice_id = ic.id left join " +
"account_account a on t.account_id = a.id left join account_account ap on a.parent_id = ap.id where (ic.state = 'open' and journal_id in %s and partner_id in %s and (ic.date_invoice between %s and %s)) or (ic.state = 'paid' and journal_id in %s and " + "
"partner_id in %s and (ic.date_invoice between %s and %s)) GROUP BY a.parent_id, ap.code, ap.name order by ap.code", (tuple(journals), tuple(partners), self.date_start, self.date_ende, tuple(journals), tuple(partners), self.date_start, self.date_end))
           dataaccount = self._cr.dictfetchall()
           for account in dataaccount:"""
           for tax in taxes:
             if journals:
              if partners:
               self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as " + 
"type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join " + 
"account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where " +
"(i.state = 'open' and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.journal_id in %s and i.partner_id in %s) or (i.state = 'paid' and lt.tax_id = %s " +
"and (i.date_invoice between %s and %s) and i.journal_id in %s and i.partner_id in %s) order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, " +
"type", (tax, self.date_start, self.date_end, tuple(journals), tuple(partners), tax, self.date_start, self.date_end, tuple(journals), tuple(partners)))
              else:
               self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as " + 
"type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join " + 
"account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where " +
"(i.state = 'open' and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.journal_id in %s) or (i.state = 'paid' and lt.tax_id = %s " +
"and (i.date_invoice between %s and %s) and i.journal_id in %s)  order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, " +
"type", (tax, self.date_start, self.date_end, tuple(journals), tax, self.date_start, self.date_end, tuple(journals)))
               """self._cr.execute("SELECT  a.parent_id as cuenta, ap.code as code, ap.name as descripcion, sum(t.tax_amount) as cuota, " + "sum(t.base_amount) as base FROM account_invoice_tax t inner join account_invoice ic on t.invoice_id = ic.id left join " +
"account_account a on t.account_id = a.id left join account_account ap on a.parent_id = ap.id where (ic.state = 'open' and " +
"journal_id in %s and (ic.date_invoice between %s and %s)) or (ic.state = 'paid' and journal_id in %s and (ic.date_invoice between %s and %s)) GROUP BY a.parent_id, ap.code, ap.name order by ap.code", (tuple(journal_ids), wiz.date_from, wiz.date_to, tuple(journal_ids), wiz.date_from, wiz.date_to))"""
             else:
              if partners:
               self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type " +
"as type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join " +
"account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where " + 
"(i.state = 'open' and lt.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s) or (i.state = 'paid' and lt.tax_id in %s and (i.date_invoice between %s and %s)) and i.partner_id in %s" + 
"order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, type", (tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(taxes), self.date_start, self.date_end, tuple(partners)))
              else:
               self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type " +
"as type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join " +
"account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where " + 
"(i.state = 'open' and lt.tax_id in %s and (i.date_invoice between %s and %s)) or (i.state = 'paid' and lt.tax_id in %s and (i.date_invoice between %s and %s)) " + 
"order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, type", (tuple(taxes), self.date_start, self.date_end, tuple(taxes), self.date_start, self.date_end))
             data3 = self._cr.dictfetchall()
             regr = False
             for rimpfac in data3:
                if rimpfac['type'] == 'out_invoice' or rimpfac['type'] == 'in_invoice':
                 #crear registro factura
                 rimpfact = {
                   'management_id': self.id,
                   'ref': 'TOTAL IMPUESTO',
                   'tax_id': rimpfac['impuesto'], 
                   'amount_untaxed': rimpfac['base'],
                   'amount_tax': rimpfac['cuota'],
                   'amount_total_untaxed': rimpfac['base'] or 0.0,
                   'amount_total_tax': rimpfac['cuota'] or 0.0,
                 }
                 regr = self.env['estructure.tax.line'].create(rimpfact)
                 #raise Warning(regr)
                else:
                 if regr and rimpfac['type'] != 'proforma':
                  #modificar registro factura
                  mimpfact = {
                   'amount_refund_untaxed': rimpfac['base'],
                   'amount_refund_tax': rimpfac['cuota'],
                   'amount_total_untaxed': regr.amount_untaxed -  rimpfac['base'] or 0.0,
                   'amount_total_tax': regr.amount_tax - rimpfac['cuota'] or 0.0,
                  }
                  regr.write(mimpfact)
        else:
         raise UserError(_('Rellene los impuestos a consultar')) 

    def calculate_detail_taxes(self):
        for rec in self:
            tax_model = self.env['account.tax']
            taxes = [x.id for x in self.tax_ids]
            journals = [x.id for x in self.journal_ids]
            partners = [x.id for x in self.partner_ids]
            if taxes and journals:
              if partners:
                self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l " + 
"on lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join " +
"res_partner rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and tax.id in %s and (i.date_invoice between %s " + 
"and %s) and i.journal_id in %s and i.partner_id in %s) or (i.state = 'paid' and tax.id in %s and (i.date_invoice between %s and %s) and i.journal_id in %s and i.partner_id in %s) group by i.id, i.number, " +
"i.type, i.date_invoice, i.partner_id, rp.name, rp.vat, i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(journals), tuple(partners), tuple(taxes), self.date_start, self.date_end, tuple(journals), tuple(partners)))  
              else:
                self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l " + 
"on lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join " +
"res_partner rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and tax.id in %s and (i.date_invoice between %s " + 
"and %s) and i.journal_id in %s) or (i.state = 'paid' and tax.id in %s and (i.date_invoice between %s and %s) and i.journal_id in %s) group by i.id, i.number, " +
"i.type, i.date_invoice, i.partner_id, rp.name, rp.vat, i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(journals), tuple(taxes), self.date_start, self.date_end, tuple(journals)))  
            else:
               if taxes and not journals:
                 if partners:
                  self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l on " +
"lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join res_partner " + 
"rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and tax.id in %s and (i.date_invoice between %s and %s) and partner_id in %s) or " + 
"(i.state = 'paid' and tax.id in %s and (i.date_invoice between %s and %s) and partner_id in %s) group by i.id, i.number, i.type, i.partner_id, i.date_invoice, rp.name, rp.vat, " + 
"i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(taxes), self.date_start, self.date_end, tuple(partners)))  
                 else:
                  self._cr.execute("SELECT i.id, i.number as numero, i.type as tipo, to_char(i.date_invoice, 'YYYY-MM-DD') as fecha, i.partner_id as partner, " +
"i.amount_untaxed as base, rp.name as empresa, rp.vat as cif, i.amount_total as total FROM account_invoice_line_tax lt left outer join account_invoice_line l on " +
"lt.invoice_line_id = l.id left outer join account_invoice i on l.invoice_id = i.id inner join account_invoice_tax it on i.id = it.invoice_id inner join res_partner " + 
"rp on i.partner_id = rp.id inner join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and tax.id in %s and (i.date_invoice between %s and %s)) or " + 
"(i.state = 'paid' and tax.id in %s and (i.date_invoice between %s and %s)) group by i.id, i.number, i.type, i.partner_id, i.date_invoice, rp.name, rp.vat, " + 
"i.amount_untaxed, i.amount_total order by i.type, i.number", (tuple(taxes), self.date_start, self.date_end, tuple(taxes), self.date_start, self.date_end))  
               else:
                 raise UserError(_('Rellene los impuestos a consultar'))
            data = self._cr.dictfetchall()
            for ele in data:
                #crear registro factura
                if ele['tipo'] == 'out_refund' or ele['tipo'] == 'in_refund':
                 factura = {
                   'management_id': self.id,
                   'ref': ele['numero'],
                   'type': 'Abono', #ele['tipo'],
                   'invoice_date': ele['fecha'],
                   'partner_id': ele['partner'],
                   'vat_number': ele['cif'],
                   'invoice_id': ele['id'],
                   'amount_refund_untaxed': -ele['base'],
                   #'amount_tax': ele[''],
                   'amount_total': -ele['total'],
                 }
                else:
                 if ele['tipo'] == 'out_invoice':
                    tip = 'Venta'
                 else:
                    tip = 'Compra'
                 factura = {
                   'management_id': self.id,
                   'ref': ele['numero'],
                   'type': tip, #ele['tipo'],
                   #'comment': ele[''],
                   #'line_type': ,
                   'invoice_date': ele['fecha'],
                   'partner_id': ele['partner'],
                   'vat_number': ele['cif'],
                   'invoice_id': ele['id'],
                   #'move_id': ,
                   #'tax_id': ,
                   'amount_untaxed': ele['base'],
                   #'amount_tax': ele[''],
                   'amount_total': ele['total'],
                 }
                #raise Warning(factura)
                reg = self.env['estructure.tax.line'].create(factura)
                if reg:
                 #buscar las lineas de impuestos de esa factura
                 idfactura = ele['id']
                 self._cr.execute("SELECT tax_id as impuesto, name as nombreimpuesto, base as base, amount as cuota from account_invoice_tax where invoice_id =  %s", (idfactura,))
                 data2 = self._cr.dictfetchall()
                 for impfac in data2:
                   if ele['tipo'] == 'out_refund' or ele['tipo'] == 'in_refund':
                    impfact = {
                     'management_id': self.id,
                     #'ref': ele['numero'],
                     #'type': ele['tipo'],
                     #'comment': ele[''],
                     #'line_type': ,
                     #'invoice_date': ele['fecha'],
                     #'partner_id': ele[''],
                     #'vat_number': ele['cif'],
                     'invoice_id': idfactura,
                     #'move_id': ,
                     'tax_id': impfac['impuesto'], 
                     'amount_untaxed': -impfac['base'],
                     'amount_tax': -impfac['cuota'],
                     #'amount_total': ele['amount_total'],
                    }
                   else:
                    #crear registro factura
                    impfact = {
                     'management_id': self.id,
                     #'ref': ele['numero'],
                     #'type': ele['tipo'],
                     #'comment': ele[''],
                     #'line_type': ,
                     #'invoice_date': ele['fecha'],
                     #'partner_id': ele[''],
                     #'vat_number': ele['cif'],
                     'invoice_id': idfactura,
                     #'move_id': ,
                     'tax_id': impfac['impuesto'], 
                     'amount_untaxed': impfac['base'],
                     'amount_tax': impfac['cuota'],
                     #'amount_total': ele['amount_total'],
                    }
                   regd = self.env['estructure.tax.line'].create(impfact)
            #BUSCAR EL RESUMEN DE IVAS
            tax_model = self.env['account.tax']
            for tax in taxes:
                if journals:
                 if partners:
                  self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt " + 
"right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' " + 
" and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.journal_id in %s and i.partner_id in %s) or (i.state = 'paid' and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.journal_id in %s and i.partner_id in %s)  order by it.invoice_id, " +
" it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, type", (tax, self.date_start, self.date_end, tuple(journals), tuple(partners), tax, self.date_start, self.date_end, tuple(journals), tuple(partners)))
                 else:
                  self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer join " +
"account_invoice_line l on lt.invoice_line_id = l.id right outer join account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and lt.tax_id = %s " +
"and (i.date_invoice between %s and %s) and i.journal_id in %s) or (i.state = 'paid' and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.journal_id in %s)  order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by " +
"impuesto, type", (tax, self.date_start, self.date_end, tuple(journals), tax, self.date_start, self.date_end, tuple(journals)))
                else:
                  if partners:
                   self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as type, it.base as base, it.amount as cuota FROM account_invoice_line_tax lt right outer " + 
"join account_invoice_line l on lt.invoice_line_id = l.id right outer join account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id left join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and " +
"lt.tax_id = %s and (i.date_invoice between %s and %s) and i.partner_id in %s) or (i.state = 'paid' and lt.tax_id = %s and (i.date_invoice between %s and %s) and i.partner_id in %s)  order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto " +
", type order by impuesto, type", (tax, self.date_start, self.date_end, tuple(partners), tax, self.date_start, self.date_end, tuple(partners)))
                  else:
                   self._cr.execute("SELECT impuesto, type, sum(base) as base, sum(cuota) as cuota from (SELECT distinct it.invoice_id, it.tax_id as impuesto, i.type as type, it.base as base, it.amount as cuota " +
"FROM account_invoice_line_tax lt right outer join account_invoice_line l on lt.invoice_line_id = l.id right outer join account_invoice i on l.invoice_id = i.id right join account_invoice_tax it on i.id = it.invoice_id " +
"left join account_tax tax on lt.tax_id = tax.id where (i.state = 'open' and lt.tax_id = %s and (i.date_invoice between %s and %s)) or (i.state = 'paid' and lt.tax_id = %s " +
"and (i.date_invoice between %s and %s))  order by it.invoice_id, it.tax_id, i.type) as totalivas group by impuesto, type order by impuesto, type", (tax, self.date_start, self.date_end, tax, self.date_start, self.date_end))
                data3 = self._cr.dictfetchall()
                regr = False
                for rimpfac in data3:
                 if rimpfac['type'] == 'out_invoice' or rimpfac['type'] == 'in_invoice':
                  #crear registro factura
                  rimpfact = {
                   'management_id': self.id,
                   'ref': 'TOTAL IMPUESTO',
                   'tax_id': rimpfac['impuesto'], 
                   'amount_untaxed': rimpfac['base'],
                   'amount_tax': rimpfac['cuota'],
                   'amount_total_untaxed': rimpfac['base'] or 0.0,
                   'amount_total_tax': rimpfac['cuota'] or 0.0,
                  }
                  regr = self.env['estructure.tax.line'].create(rimpfact)
                  #raise Warning(regr)
                 else:
                  if regr and rimpfac['type'] != 'proforma':
                   #modificar registro factura
                   mimpfact = {
                   'amount_refund_untaxed': rimpfac['base'],
                   'amount_refund_tax': rimpfac['cuota'],
                   'amount_total_untaxed': regr.amount_untaxed -  rimpfac['base'] or 0.0,
                   'amount_total_tax': regr.amount_tax - rimpfac['cuota'] or 0.0,
                   }
                   regr.write(mimpfact)
            """raise UserError(_('No EAT Tax Mapping was found'))"""
    #resumen de IVA
    def calculate_taxes_iva_summary(self):
      if self.state == 'draft':
        if self.tax_ids:
         for rec in self:
          tax_model = self.env['account.tax']
          taxes = [x.id for x in self.tax_ids]
          journals = [x.id for x in self.journal_ids]
          partners = [x.id for x in self.partner_ids]
          #BUSCAR APLICACIONES IMPUESTOS
          self._cr.execute("SELECT t.type_tax_use as type, sum(it.base) as base, sum(it.amount) as cuota FROM account_tax t inner join account_invoice_tax it on t.id = it.tax_id inner join account_invoice i on it.invoice_id = i.id and " +
"(i.date_invoice between %s and %s) inner join type_taxes_information tti on t.type_taxes_information_id = tti.id and tti.exclude = 'n'  where t.id in %s group by t.type_tax_use", (self.date_start, self.date_end, tuple(taxes),))
          types = self._cr.dictfetchall()
          for type in types:
           #grabar registro tipo aplicacion impuesto
           """rtaplimp = {
                   'management_id': self.id,
                   'ref': 'TIPO' + str(type['type']),
                   #'amount_total_untaxed': type['base'] or 0.0,
                   #'amount_total_tax': type['cuota'] or 0.0,
           }
           regtipo = self.env['estructure.tax.line'].create(rtaplimp)"""
           #BUSCAR ACCOUNT.TAX.GROUPS DE LOS IMPUESTOS.
           self._cr.execute("SELECT tax.type_taxes_information_id as group, sum(it.base) as base, sum(it.amount) as cuota FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax " +
"on it.tax_id = tax.id inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id and tti.exclude = 'n' where (i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s and " +
"tti.exclude = 'n') or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s and tti.exclude = 'n') " +
"group by tax.type_taxes_information_id", (tuple(taxes), self.date_start, self.date_end, type['type'], tuple(taxes), self.date_start, self.date_end, type['type']))
           #self._cr.execute("SELECT t.type_taxes_information_id as group, sum(it.base) as base, sum(it.amount) as cuota FROM account_tax t inner join account_invoice_tax it on t.id = it.tax_id inner join type_taxes_information tti on t.type_taxes_information_id = tti.id inner join account_invoice i on it.invoice_id = i.id and (i.date_invoice between %s and %s) where " +
#"t.id in %s and tti.type_tax_use = %s group by t.type_taxes_information_id", (self.date_start, self.date_end, tuple(taxes), type['type']))
           groups = self._cr.dictfetchall()
           sumbase = 0.0
           sumcuota = 0.0
           for group in groups:
            """sumbase = float(group['base']) or 0.0
            sumcuota = float(group['cuota']) or 0.0
            #buscar si hay alguno en este grupo con base a excluir
            self._cr.execute("SELECT tax.type_taxes_information_id as group, sum(it.base) as base, sum(it.amount) as cuota FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax " +
"on it.tax_id = tax.id inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id and tti.exclude_amount_untaxes = 's' and tti.exclude = 'n' and tti.id = %s where (i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s) " +
"group by tax.type_taxes_information_id", (group['group'], tuple(taxes), self.date_start, self.date_end, type['type'], tuple(taxes), self.date_start, self.date_end, type['type']))
            regexclbase = self._cr.dictfetchall()
            for excl in regexclbase:
               sumbase = sumbase - float(excl['base'])
            #buscar si hay algun abono en este grupo
            self._cr.execute("SELECT tax.type_taxes_information_id as group, sum(it.base) as base, sum(it.amount) as cuota FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id  and i.state in ('out_refund', 'in_refund') inner join account_tax tax " +
"on it.tax_id = tax.id inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id and tti.exclude_amount_untaxes = 's' and tti.exclude = 'n' and tti.id = %s where (i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and tti.type_tax_use = %s) " +
"group by tax.type_taxes_information_id", (group['group'], tuple(taxes), self.date_start, self.date_end, type['type'], tuple(taxes), self.date_start, self.date_end, type['type']))
            regabonobase = self._cr.dictfetchall()
            raise Warning(regabonobase)
            for abono in regabonobase:
               sumbase = sumbase - float(abono['base'])
               sumcuota = sumcuota - float(abono['cuota'])"""
            #grabar registro grupo
            #buscar nombre del tipo de grupo informativo
            """namegroup = self.env['type.taxes.information'].browse(group['group']).name
            rgroup = {
                   'management_id': self.id,
                   'ref': namegroup,
                   'group_id': group['group'],
                   #'amount_total_tax': group['cuota'] or 0.0,
            }
            reggroup = self.env['estructure.tax.line'].create(rgroup)"""
            if journals:
              if partners:
               self._cr.execute("SELECT it.tax_id as impuesto, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"(i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s and i.journal_id in %s) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s and i.journal_id in %s)" +
"group by it.tax_id, tti.exclude_amount_untaxes, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(journals), tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(journals)))
              else:
               self._cr.execute("SELECT it.tax_id as impuesto, i.type as type, tt.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"(i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.journal_id in %s) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.journal_id in %s)" +
"group by it.tax_id, tti.exclude_amount_untaxes, tti.id, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(journals), tuple(taxes), self.date_start, self.date_end, tuple(journals)))
            else:
              if partners:
               self._cr.execute("SELECT it.tax_id as impuesto, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"(i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s) and i.partner_id in %s)" +
"group by it.tax_id, tti.exclude_amount_untaxes, tti.id, i.type order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(partners), tuple(taxes), self.date_start, self.date_end, tuple(partners)))

              else:
               #raise Warning(group['group'])
               self._cr.execute("SELECT it.tax_id as impuesto, i.type as type, tti.id as group, sum(it.base) as base, sum(it.amount) as cuota, tti.exclude_amount_untaxes as exclude_base FROM account_invoice_tax it inner join account_invoice i on it.invoice_id = i.id inner join account_tax tax on it.tax_id = tax.id and tax.type_taxes_information_id = %s inner join type_taxes_information tti on tax.type_taxes_information_id = tti.id where " +
"(i.state = 'open' and it.tax_id in %s and (i.date_invoice between %s and %s)) or (i.state = 'paid' and it.tax_id in %s and (i.date_invoice between %s and %s))" +
"group by it.tax_id, tti.exclude_amount_untaxes, i.type, tti.id order by it.tax_id, i.type", (group['group'], tuple(taxes), self.date_start, self.date_end, tuple(taxes), self.date_start, self.date_end))
            data3 = self._cr.dictfetchall()
            #raise Warning(data3)
            regr = False
            for rimpfac in data3:
                 amounttotal = 0.0
                 if rimpfac['exclude_base'] == 'n':
                    amounttotal = rimpfac['base']
                 if rimpfac['type'] == 'out_invoice' or rimpfac['type'] == 'in_invoice':
                  #crear registro factura
                  rimpfact = {
                   'management_id': self.id,
                   #'ref': 'TOTAL IMPUESTO',
                   'tax_id': rimpfac['impuesto'], 
                   'amount_untaxed': amounttotal,
                   'amount_tax': rimpfac['cuota'],
                   'amount_total_untaxed': amounttotal or 0.0,
                   'amount_total_tax': rimpfac['cuota'] or 0.0,
                   'group_id': rimpfac['group'],
                  }
                  if amounttotal < 0:
                     sumbase = sumbase - amounttotal
                  else:
                     sumbase = sumbase + amounttotal
                  if rimpfac['cuota'] < 0:
                     sumcuota = sumcuota - rimpfac['cuota'] or 0.0
                  else:
                     sumcuota = sumcuota + rimpfac['cuota'] or 0.0
                  regr = self.env['estructure.tax.line'].create(rimpfact)
                  #raise Warning(regr)
                 else:
                  if regr and rimpfac['type'] != 'proforma':
                   #modificar registro factura
                   mimpfact = {
                   'amount_refund_untaxed': amounttotal,
                   'amount_refund_tax': rimpfac['cuota'],
                   'amount_total_untaxed': regr.amount_untaxed -  amounttotal or 0.0,
                   'amount_total_tax': regr.amount_tax - rimpfac['cuota'] or 0.0,
                  }
                  sumbase = sumbase - amounttotal
                  sumcuota = sumcuota - rimpfac['cuota'] or 0.0
                  regr.write(mimpfact)
            #buscar nombre del tipo de grupo informativo
            namegroup = self.env['type.taxes.information'].browse(group['group']).name
            rgroup = {
                   'management_id': self.id,
                   'ref': 'TOTAL ' + namegroup,
                   'amount_total_untaxed': sumbase or 0.0,
                   'amount_total_tax': sumcuota or 0.0,
                   'group_id': group['group'],
            }
            reggroup = self.env['estructure.tax.line'].create(rgroup)
         self._cr.execute("SELECT t.type_tax_use as type, sum(e.amount_total_untaxed) as amount_untaxed, sum(e.amount_total_tax) as tax FROM estructure_tax_line e inner join type_taxes_information t on e.group_id = t.id and t.include_tax_diferent = 's' where e.tax_id is null and e.amount_total_untaxed is not null and e.amount_total_tax is not null and e.management_id = %s group by t.type_tax_use order by t.type_tax_use desc", (self.id, ))
         diferentsgroups = self._cr.dictfetchall()
         #raise Warning(diferentsgroups)
         diferentsb = 0.0
         diferentsc = 0.0
         for dgroup in diferentsgroups:
             rimpfactx = {
               'management_id': self.id,
               'ref': 'TOTAL ' + str(dgroup['type']),
               'amount_total_untaxed':  dgroup['amount_untaxed'] or 0.0,
               'amount_total_tax': dgroup['tax'] or 0.0,
             }
             regr = self.env['estructure.tax.line'].create(rimpfactx)

             if diferentsb == 0.0:
                diferentsb = dgroup['amount_untaxed']
             else:
                diferentsb = diferentsb - dgroup['amount_untaxed']
             if diferentsc == 0.0:
                diferentsc = dgroup['tax']
             else:
                diferentsc = diferentsc - dgroup['tax']
         rimpfact = {
               'management_id': self.id,
               'ref': 'Diferencia',
               'amount_total_untaxed': diferentsb or 0.0,
               'amount_total_tax': diferentsc or 0.0,
         }
         regr = self.env['estructure.tax.line'].create(rimpfact)
        else:
         raise UserError(_('Rellene los impuestos a consultar'))


    @api.multi
    def btn_account_journal(self):
        #res = self.calculate_journal()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res
    @api.multi
    def btn_sumsandbalances(self):
        #res = self.calculate_sumsandbalances()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res
    @api.multi
    def btn_taxes_summary(self):
        res = self.calculate_taxes_summary()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res
    @api.multi
    def btn_detail_taxes(self):
        res = self.calculate_detail_taxes()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res
    @api.multi
    def btn_taxes_iva_summary(self):
        res = self.calculate_taxes_iva_summary()
        self.write({'state': 'calculated',
                    'calculation_date': fields.Datetime.now()})
        return res

    @api.multi
    def export_xlsx(self):
        self.ensure_one()
        context = dict(self.env.context, active_ids=self.ids)
        """raise Warning({
            'name': 'Details Taxes XLSX report',
            'model': 'management.fiscal.accounting.information',
            'type': 'ir.actions.report',
            'report_name': 'management_fiscal_accounting_information.details_taxes_xlsx',
            'report_type': 'xlsx',
            'report_file': 'details.vat.book',
            'context': context,
        })"""
        return {
            'name': 'Details Taxes XLSX report',
            'model': 'management_fiscal_accounting_information.ManagementFiscalAccountingInformation',
            'type': 'ir.actions.report',
            'report_name': 'management_fiscal_accounting_information.details_taxes_xlsx',
            'report_type': 'xlsx',
            #'report_file': 'details.vat.book',
            'context': context,
        }
