# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError, UserError

class Phong(models.Model):
    _name = 'phong'
    _order = 'name'

    name            = fields.Char('Tên phòng', size=256, required=True)
    code            = fields.Char('Code', required=True)
    hieu_dien_the   = fields.Float('Hiệu điện thế', default=220)
    nhiet_do_co_ban = fields.Float('Nhiệt độ cơ bản', digits=(2, 2), default=18.00, required=True)

Phong()


class DieuHoa(models.Model):
    _name = 'dieuhoa'
    _order = 'name'

    @api.one
    def _compute_dien_nang_tieu_thu_kh(self):
        self.dien_nang_tieu_thu_kh = self.dien_nang_tieu_thu * 1000 / 3600

    name            = fields.Char('Tên máy', size=64, required=True)
    code            = fields.Char('Code', required=True)
    phong_id        = fields.Many2one('phong', string='Phòng')
    nhiet_do_co_ban = fields.Float(related='phong_id.nhiet_do_co_ban', readonly=True)
    hieu_dien_the   = fields.Float(related='phong_id.hieu_dien_the', readonly=True)

    trang_thai      = fields.Selection([('on', 'Bật'), ('off', 'Tắt')], 'Trạng thái', default='off')

    gia_tri         = fields.Integer('Nhiệt độ hiện tại', help='Thông số hiện tại của máy')
    nhiet_do_phong  = fields.Float('Nhiệt độ phòng', help='Nhiệt độ phòng hiện tại đo được')

    dien_nang_tieu_thu      = fields.Float('Tổng điện năng tiêu thụ (W/s)', digits=(30, 2), default=0)
    dien_nang_tieu_thu_kh   = fields.Float('Tổng điện năng tiêu thụ (Kwh)')

    nhiet_do_nho_nhat   = fields.Float('Nhiệt độ nhỏ nhất', digits=(2, 2), default=16.00, required=True)
    nhiet_do_cao_nhat   = fields.Float('Nhiệt độ lớn nhất', digits=(2, 2), default=30.00, required=True)

    lan_cap_nhat_cuoi   = fields.Datetime('Lần cập nhật cuối')

    control_state       = fields.Boolean('State')

    @api.one
    def turn_on(self):
        self.lan_cap_nhat_cuoi = fields.Datetime.now()
        self.trang_thai = 'on'
        self.gia_tri = 0
        self.control_state = True

    @api.one
    def turn_off(self):
        self.lan_cap_nhat_cuoi = False
        self.trang_thai = 'off'
        self.control_state = True

    @api.model
    def find_by_code(self, code):
        return self.search([('code', '=', code)], limit=1) or False

    @api.multi
    def calc_control(self, nhiet_do_phong):
        self.ensure_one()

        dieu_chinh = -2 if nhiet_do_phong > self.nhiet_do_co_ban else 2 if nhiet_do_phong < self.nhiet_do_co_ban else 0

        if self.gia_tri == 0:
            return self.nhiet_do_cao_nhat - self.nhiet_do_nho_nhat

        print dieu_chinh, self.gia_tri+dieu_chinh

        if dieu_chinh != 0 and (self.gia_tri+dieu_chinh > self.nhiet_do_cao_nhat or self.gia_tri+dieu_chinh < self.nhiet_do_nho_nhat):
            return 0

        # if self.gia_tri <= self.nhiet_do_nho_nhat and self.gia_tri > nhiet_do_phong:
        #     return False

        # if self.gia_tri >= self.nhiet_do_cao_nhat and self.gia_tri < nhiet_do_phong:
        #     return False

        if abs(nhiet_do_phong - self.nhiet_do_co_ban) < 0.5:
            return 0

        return dieu_chinh


DieuHoa()


class GiaTri(models.Model):
    _name = 'giatri'
    _order = 'create_date desc'

    dieuhoa_id      = fields.Many2one('dieuhoa', string='Điều hòa', required=True)
    nhiet_do_phong  = fields.Float('Nhiệt độ phòng', help='Nhiệt độ phòng hiện tại đo được', required=True)
    dong_dien       = fields.Float('Cường độ', default=0)
    gia_tri         = fields.Integer('Nhiệt độ hiện tại')
    dieu_chinh      = fields.Integer('Điều chỉnh', default=0, help='Thông tin điều khiển thiết bị')

    @api.model
    def create(self, val):

        dieuhoa = self.env['dieuhoa'].browse(val.get('dieuhoa_id', False))
        if not dieuhoa:
            raise ValidationError('Dữ liệu không hợp lệ!')
        if dieuhoa.trang_thai == 'off':
            raise ValidationError('Máy đã tắt!')

        giatri_saptoi = dieuhoa.gia_tri + val.get('dieu_chinh', 0)
        # if giatri_saptoi < dieuhoa.nhiet_do_nho_nhat or giatri_saptoi > dieuhoa.nhiet_do_cao_nhat:
        #     raise ValidationError('Ngoài phạm vi điều chỉnh')

        val.update({'gia_tri': dieuhoa.gia_tri})
        res = super(GiaTri, self).create(val)

        lan_cap_nhat_cuoi   = res.create_date
        dien_nang_tieu_thu  = dieuhoa.dien_nang_tieu_thu or 0
        dong_dien           = res.dong_dien
        hieu_dien_the       = dieuhoa.hieu_dien_the
        thoi_gian = ( fields.Datetime.from_string(res.create_date) - fields.Datetime.from_string(dieuhoa.lan_cap_nhat_cuoi) ).total_seconds()

        dien_nang_tieu_thu += (hieu_dien_the * dong_dien * thoi_gian)

        if giatri_saptoi > dieuhoa.nhiet_do_cao_nhat:
            giatri_saptoi = dieuhoa.nhiet_do_cao_nhat
        if giatri_saptoi < dieuhoa.nhiet_do_nho_nhat:
            giatri_saptoi = dieuhoa.nhiet_do_nho_nhat

        res.dieuhoa_id.write({
            'dien_nang_tieu_thu':   dien_nang_tieu_thu,
            'nhiet_do_phong':       res.nhiet_do_phong,
            'lan_cap_nhat_cuoi':    lan_cap_nhat_cuoi,
            'gia_tri':              giatri_saptoi,
            'control_state':        False,
        })
        return res

GiaTri()