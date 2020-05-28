import logging
import json
import re

from django import http
from django.views import View
from .models import User
from django_redis import get_redis_connection
from django.contrib.auth import login

logger = logging.getLogger('django')


# Create your views here.
class UsernameCountView(View):
    """判断用户名是否重复注册"""

    def get(self, request, username):
        '''
        判断用户名是否重复
        :param request:
        :param username:
        :return:
        '''
        # 查询用户名在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '访问数据库失败'})
        return http.JsonResponse({'code': 0, 'errmsg': 'ok', 'count': count})


class MobileCountView(View):
    """判断手机号是否重复注册"""

    def get(self, request, mobile):
        '''判断手机是否重复'''
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '访问数据库错误'})
        return http.JsonResponse({'code': 400, 'errmsg': 'ok', 'count': count})


class RegisterView(View):
    """用户注册"""

    # 接收参数
    def post(self, request):
        json_bytes = request.body  # 获取原始的json数据
        json_str = json_bytes.decode()  # 对获取的json解析成json字符串
        json_dict = json.loads(json_str)  # 将json字符串转换成标准的python字典

        # 获取数据
        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        allow = json_dict.get('allow')
        sms_code_client = json_dict.get('sms_code')

        # 校验参数
        # 校验整体
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        # 用户名校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400, 'errmsg': '用户名格式错误'})

        # 密码校验
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': '密码格式错误'})

        # 密码二次校验
        if password2 != password:
            return http.JsonResponse({'code': 400, 'errmsg': '两次输入不一致'})

        # 手机号校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '手机号格式错误'})

        # 协议校验
        if not allow:
            return http.JsonResponse({'code': 400, 'errmsg': '未同意协议'})

        # 短信验证
        redis_conn = get_redis_connection('verify_code')
        # 获取验证码
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断验证码是否存在
        if not sms_code_server:
            return http.JsonResponse({'code': 400, 'errmsg': '验证码过期'})

        # 对比验证码
        if sms_code_server.decode() != sms_code_client:
            return http.JsonResponse({'code': 400, 'errmsg': '验证码错误'})

        # 实现业务逻辑
        # 将注册的用户保存到数据库
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '保存数据库出错'})

        # 保存注册登录状态
        login(request, user)

        # 返回结果
        return http.JsonResponse({'code': 0, 'errmsg': 'ok'})
