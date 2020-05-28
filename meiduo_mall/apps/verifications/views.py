from django.shortcuts import render
from verifications.libs.captcha.captcha import captcha
from django import http
from django_redis import get_redis_connection
from django.views import View
from verifications.libs.yuntongxun.ccp_sms import CCP
import random, logging
logger = logging.getLogger('django')


# Create your views here.
class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        # 接收参数
        # 调用captcha工具生成图形码和文字
        text, image = captcha.generate_captcha()

        # 链接redis，获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 利用链接对象保存数据到redis，用setex，因为set不能设置有效时间
        redis_conn.setex('img_%s' % uuid, 300, text)

        # 返回结果
        return http.HttpResponse(image, content_type='image/jpg')
        # 校验参数
        # 实现逻辑


class SMSCodeView(View):
    """短信验证码"""

    # 请求方式get
    # 请求地址http://www.meiduo.site:8000/sms_codes/<mobile:mobile>/
    # 必传参数mobile
    def get(self, request, mobile):
        # 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        # 实现逻辑
        # 建立链接
        redis_conn = get_redis_connection('verify_code')
        # 服务器获取验证码
        image_code_server = redis_conn.get('img_%s' % uuid)

        # 判断验证码是否存在
        if image_code_server is None:
            return http.JsonResponse({'code': 400, 'errmsg': '验证码过期'})

        # 删除验证码,避免恶意刷验证码
        redis_conn.delete('img_%s' % uuid)

        # 因为从redis读取是bytes数据类型要转为字符串
        image_code_server = image_code_server.decode()

        # 验证码进行判断
        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': 400, 'errmsg': '图形验证码错误'})

        # 生成验证码
        sms_code = '%06d' % random.randint(0, 999999)
        # 把验证码写入日志
        logger.info(sms_code)

        # 设置验证码有效期限
        redis_conn.setex('sms_%s' % mobile, 300, 1)

        # 发送验证码
        # CCP().send_template_sms('手机号码', ['验证码', '有效期'], '短信模板')
        CCP().send_template_sms('17704026367', [sms_code, 5], 1)

        # 返回结果
        return http.JsonResponse({'code': 0, 'errmsg': '发送验证码成功'})
