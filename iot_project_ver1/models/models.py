# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class ThongKe(models.Model):
    _name = 'thongke'

    name        = fields.Integer('Name')
    thoi_gian   = fields.Datetime('Thoi gian', default=fields.Datetime.now())
    nhiet_do    = fields.Float('Nhiet do', digits=(2, 2))
    do_am       = fields.Float('Do am', digits=(2, 2))
    anh_sang    = fields.Float('Anh sang', digits=(2, 2))

    @api.model
    def create(self, vals):
        data = self.search([], order='name desc', limit=1)
        name =  data.name + 1 if data else 1
        vals['name'] = name
        res = super(ThongKe, self).create(vals)

        Baocao = self.env['baocao']
        Baocao.create({
            'name':     vals['name'],
            'loai':     '0',
            'gia_tri':  vals['nhiet_do'],
        })

        Baocao.create({
            'name':     vals['name'],
            'loai':     '1',
            'gia_tri':  vals['do_am'],
        })

        Baocao.create({
            'name':     vals['name'],
            'loai':     '2',
            'gia_tri':  vals['anh_sang'],
        })

        return res

ThongKe()

class BaoCao(models.Model):
    _name = 'baocao'
    
    name    = fields.Char('Name')
    loai    = fields.Selection([('0', 'Nhiet do'), ('1', 'Do am'), ('2', 'Anh sang')], 'Loai')
    gia_tri = fields.Float('Gia Tri', digits=(2, 2))