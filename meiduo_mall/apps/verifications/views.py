from django.shortcuts import render
from verifications.libs.captcha.captcha import captcha
from django import http
from django_redis import get_redis_connection
from django.views import View

# Create your views here.
class ImageCodeView(View):
    """图形验证码"""
    def get(self,request,uuid):
        # 接收参数
        # 调用captcha工具生成图形码和文字
        text,image = captcha.generate_captcha()

        # 链接redis，获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 利用链接对象保存数据到redis，用setex，因为set不能设置有效时间
        redis_conn.setex('img_%s'% uuid, 300, text)

        # 返回结果
        return http.HttpResponse(image, content_type='image/jpg')
        # 校验参数
        # 实现逻辑
