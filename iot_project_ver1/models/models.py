# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from datetime import datetime
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

import smbus
import time
DEVICE     = 0x23 # Default device I2C address
POWER_DOWN = 0x00 # No active state
POWER_ON   = 0x01 # Power on
RESET      = 0x07 # Reset data register value
CONTINUOUS_LOW_RES_MODE = 0x13
CONTINUOUS_HIGH_RES_MODE_1 = 0x10
CONTINUOUS_HIGH_RES_MODE_2 = 0x11
ONE_TIME_HIGH_RES_MODE_1 = 0x20
ONE_TIME_HIGH_RES_MODE_2 = 0x21
ONE_TIME_LOW_RES_MODE = 0x23
bus = smbus.SMBus(1)  
 
def convertToNumber(data):
    return ((data[1] + (256 * data[0])) / 1.2)
 
def readLight(addr=DEVICE):
    data = bus.read_i2c_block_data(addr,ONE_TIME_HIGH_RES_MODE_1)
    return convertToNumber(data)

class QuanLy(models.Model):
    _name = 'quanly'

    name        = fields.Char('Tên dự án')
    code        = fields.Char('Code')
    thietbi_ids = fields.One2many('thietbi', 'project_id', 'Danh sách thiết bị')
    thoi_gian   = fields.Char('Lần cập nhật cuối', readonly=True)
    nhiet_do    = fields.Float('Nhiệt độ', digits=(2, 2), readonly=True)
    do_am       = fields.Float('Độ ẩm', digits=(2, 2), readonly=True)
    anh_sang    = fields.Float('Ánh sáng', digits=(2, 2), readonly=True)

    # @api.multi
    # def bat_den(self):
    #     self.ensure_one()
    #     for r in self.thietbi_ids:
    #         if r.code == 'den':
    #             r.turn_on()

    # @api.multi
    # def tat_den(self):
    #     self.ensure_one()
    #     for r in self.thietbi_ids:
    #         if r.code == 'den':
    #             r.turn_off()

    # @api.multi
    # def bat_moto(self):
    #     self.ensure_one()
    #     for r in self.thietbi_ids:
    #         if r.code == 'moto':
    #             r.turn_on()

    # @api.multi
    # def tat_moto(self):
    #     self.ensure_one()
    #     for r in self.thietbi_ids:
    #         if r.code == 'moto':
    #             r.turn_off()


class ThietBi(models.Model):
    _name = 'thietbi'

    name        = fields.Char('Tên thiết bị')
    code        = fields.Char('Code')
    mo_ta       = fields.Text('Mô tả')
    state       = fields.Selection([('on', 'Bật'), ('off', 'Tắt')], 'Trạng thái', default='off')
    pin         = fields.Integer('Pin', help='Chân cắm trên Raspberry.')
    is_input    = fields.Boolean('Là thiết bị đo lường')
    loai        = fields.Selection([('nhiet_do', 'Nhiệt độ'), ('do_am', 'Độ ẩm'), ('anh_sang', 'Ánh sáng')], 'Dùng để đo')
    project_id  = fields.Many2one('quanly', 'Project')

    @api.multi
    def turn_on(self):
        self.ensure_one()
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, 1)
        self.write({'state': 'on'})

    @api.multi
    def turn_off(self):
        self.ensure_one()
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, 0)
        self.write({'state': 'off'})

class ThongKe(models.Model):
    _name = 'thongke'

    name        = fields.Char('Name', default=fields.Datetime.now())
    nhiet_do    = fields.Float('Nhiệt độ', digits=(2, 2))
    do_am       = fields.Float('Độ ẩm', digits=(2, 2))
    anh_sang    = fields.Float('Ánh sáng', digits=(2, 2))

    @api.model
    def create(self, vals):
        res = super(ThongKe, self).create(vals)

        self.env['quanly'].search([]).write({
            'thoi_gian':    res['name'],
            'nhiet_do':     res['nhiet_do'],
            'do_am':        res['do_am'],
            'anh_sang':     res['anh_sang'],
        })

        Baocao = self.env['baocao']
        Baocao.create({
            'name':     res['name'],
            'loai':     '0',
            'gia_tri':  res['nhiet_do'],
        })

        Baocao.create({
            'name':     res['name'],
            'loai':     '1',
            'gia_tri':  res['do_am'],
        })

        Baocao.create({
            'name':     res['name'],
            'loai':     '2',
            'gia_tri':  res['anh_sang'],
        })

        return res

ThongKe()

class BaoCao(models.Model):
    _name = 'baocao'
    
    name    = fields.Char('Name')
    loai    = fields.Selection([('0', 'Nhiet do'), ('1', 'Do am'), ('2', 'Anh sang')], 'Loai')
    gia_tri = fields.Float('Gia Tri', digits=(2, 2))
