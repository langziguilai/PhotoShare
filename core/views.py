import http
from datetime import datetime

from django.db import IntegrityError, connection
from django.forms import model_to_dict
from django.shortcuts import render
from django.utils.timezone import now

from core.models import User, UserFollow, UserLikePost, UserPost, UserFollowBy, Post, Comment, \
    POST_STATUS_PUBLIC, PUBLIC_CHOICE

import simplejson as simplejson
from django import forms
from django.http import HttpResponse, JsonResponse

from core.settings import SESSION_USER_KEY, ROLE_POST_ADMIN, MAX_POST, MAX_COMMENT, \
    ROLE_COMMENT_ADMIN, ROLE_USER_ADMIN, MAX_USER, MAX_AVATAR_SIZE, MAX_IMAGE_SIZE, IMAGE_SIZE_SMALL, \
    IMAGE_SIZE_NORMAL, PATH_IMAGE, MAX_FILE_SIZE, PATH_FILE  # 在session中保存用户信息
from core.settings import SESSION_TIME_CAN_NEXT_LOGIN  # 在中保存用户下次准许登录时间
from core.settings import SESSION_LOGIN_FAIL_CNT  # 登录失败的次数
from core.settings import MAX_LOGIN_TIMES
from core.settings import LOGIN_FORBIDDEN_DURATION
from core.settings import CODE_SUCCESS
from core.settings import CODE_FAIL


# 用户是否已经登录
def user_has_login(request):
    return SESSION_USER_KEY in request.session


# 用户是否登录失败次数过多
def user_try_login_to_many_times(request):
    if SESSION_LOGIN_FAIL_CNT not in request.session:
        return False
    else:
        if request.session[SESSION_LOGIN_FAIL_CNT] > MAX_LOGIN_TIMES:
            if request.session[SESSION_TIME_CAN_NEXT_LOGIN] < datetime.now():
                del request.session[SESSION_TIME_CAN_NEXT_LOGIN]
                del request.session[SESSION_LOGIN_FAIL_CNT]
                return False
            return True
        return False


# 定义简单注解：需要登录
def require_login(method):
    def new_method(request, *args, **kw):
        if user_has_login(request):
            return method(request, *args, **kw)
        return response_fail({"msg": "请您先登录"})

    return new_method


# 定义简单注解：需要未登录
def require_not_login(method):
    def new_method(request, *args, **kw):
        if user_has_login(request):
            return response_success({"msg": "您已经登录"})
        return method(request, *args, **kw)

    return new_method


# 定义简单注释：方法限制
def http_method_limit(http_methods):
    def handle_func(method):
        def new_method(request, *args, **kw):
            if request.method not in http_methods:
                return response_fail({"msg": "不支持http方法:" + request.method})
            return method(request, *args, **kw)

        return new_method

    return handle_func


# 主页

@http_method_limit(http_methods=['GET'])
def index_action(request):
    if not is_request_json(request):
        return render(request, 'core/index.html')
    try:
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                posts = Post.objects.filter(). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 登录
@http_method_limit(http_methods=['POST'])
@require_not_login
def login_action(request):
    # 检查是否登录失败次数过多
    if user_try_login_to_many_times(request):
        return response_fail(msg={"msg": "您登录次数过多"})
    # 检查Form是否正确
    form_data = simplejson.loads(request.body)
    user = None
    form = LoginForm(form_data)
    if form.is_valid():
        try:
            if not is_empty_string(form_data['username']):
                user = User.objects.get(username=form_data['username'],
                                        password=encrypt_password(form_data['password']))
            elif not is_empty_string(form_data['email']):
                user = User.objects.get(email=form_data['email'], password=encrypt_password(form_data['password']))
            elif not is_empty_string(form_data['phone']):
                user = User.objects.get(phone=form_data['phone'], password=encrypt_password(form_data['password']))
            User.objects.filter(id=user.id).update(lastLogin=now())  # 更新登录日期
            posts = UserPost.objects.get(pk=user.id)
            likes = UserLikePost.objects.get(pk=user.id)
            follows = UserFollow.objects.get(pk=user.id)
            user = model_to_dict(user)
            user["password"] = ""  # 密码置空，以反之返回出去
            request.session[SESSION_USER_KEY] = user
            posts = model_to_dict(posts)
            likes = model_to_dict(likes)
            follows = model_to_dict(follows)
            return response_success(
                {"user": user, "posts": posts, "likes": likes, "follows": follows})
        except User.DoesNotExist:
            return response_fail(msg={"msg": "登录失败，用户信息和密码不匹配"})
        except:
            return response_fail(msg={"msg": "服务器发生错误，请稍后重试"})

    if SESSION_LOGIN_FAIL_CNT in request.session:
        request.session[SESSION_LOGIN_FAIL_CNT] = request.session[SESSION_LOGIN_FAIL_CNT] + 1
        if request.session[SESSION_LOGIN_FAIL_CNT] > MAX_LOGIN_TIMES:
            request.session[SESSION_TIME_CAN_NEXT_LOGIN] = datetime.now() + LOGIN_FORBIDDEN_DURATION
            return response_fail(msg={"msg": "您登录失败的次数过多，请稍候再试"})
    else:
        request.session[SESSION_LOGIN_FAIL_CNT] = 1
    return response_fail(msg={"msg": "登录失败"})


def is_empty_string(string):
    return string == ""


def encrypt_password(password):
    import hashlib
    sha1 = hashlib.sha1(password.encode('utf-8'))
    return sha1.hexdigest()


def response_fail(msg):
    msg['code'] = CODE_FAIL
    return JsonResponse(msg)


def response_success(msg):
    msg['code'] = CODE_SUCCESS
    return JsonResponse(msg)


# 登录表单
class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, min_length=6, required=False)
    email = forms.EmailField(max_length=30, min_length=6, required=False)
    phone = forms.CharField(max_length=20, min_length=6, required=False)
    password = forms.CharField(max_length=20, min_length=6, required=True)
    remember_me = forms.BooleanField(initial=False, required=False)
    duration = forms.ChoiceField(choices=((1, "一天"), (2, "一周"), (3, "一个月"), (4, "永久")), required=False)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=30, min_length=6, required=True)
    email = forms.EmailField(max_length=30, min_length=6, required=False)
    phone = forms.CharField(max_length=20, min_length=6, required=False)
    verification_code = forms.CharField(max_length=20, required=False)
    password = forms.CharField(max_length=20, min_length=6, required=True)


# 注册
@http_method_limit(http_methods=['POST'])
@require_not_login
def register_action(request):
    # 检查Form是否正确
    form_data = simplejson.loads(request.body)
    form = RegisterForm(form_data)
    if form.is_valid():
        if not is_empty_string(form_data['email']):
            try:
                user = User(username=form_data['username'], email=form_data['email'],
                            password=encrypt_password(form_data['password']), status=4)  # 未验证用户
                user.save()
                follows = model_to_dict(UserFollow.objects.create(id=user.id))
                UserFollowBy.objects.create(id=user.id)
                likes = model_to_dict(UserLikePost.objects.create(id=user.id))
                posts = model_to_dict(UserPost.objects.create(id=user.id))
                user = model_to_dict(user)
                user["password"] = ""
                request.session[SESSION_USER_KEY] = user
                send_email_verification_link(user)
                return response_success(msg={"user": user, "posts": posts, "likes": likes, "follows": follows})
            except IntegrityError:
                return response_fail(msg={"msg": "email或者用户名已经存在"})
        elif not is_empty_string(form_data['phone']) and not is_empty_string(form_data['verification_code']):
            try:
                user = User(username=form_data['username'], email=form_data['phone'],
                            password=encrypt_password(form_data['password']), status=2)  # 不活跃用户
                user.save()
                follows = model_to_dict(UserFollow.objects.create(id=user.id))
                UserFollowBy.objects.create(id=user.id)
                likes = model_to_dict(UserLikePost.objects.create(id=user.id))
                posts = model_to_dict(UserPost.objects.create(id=user.id))
                user = model_to_dict(user)
                user["password"] = ""
                request.session[SESSION_USER_KEY] = user
                return response_success(msg={"user": user, "posts": posts, "likes": likes, "follows": follows})
            except IntegrityError:
                return response_fail(msg={"msg": "电话或者用户名已经存在"})

    return response_fail(msg={"msg": "注册失败"})


# 发送手机验证码 TODO
def send_phone_verification_code_action(request):
    if 'phone' in request.POST:
        pass
    else:
        return response_fail({"msg": "参数不正确"})


# 验证手机验证码
def verify_phone_action(request):
    from core.models import RegisterConfirm
    if 'phone' in request.POST and 'code' in request.POST:
        phone = request.POST['phone']
        code = request.POST['code']
        if RegisterConfirm.objects.filter(phone=phone, phone_code=code).exists():
            RegisterConfirm.objects.filter(phone=phone, phone_code=code).delete()
            return response_success({"msg": "完成验证"})
        else:
            return response_fail({"msg": "验证码错误"})
    else:
        return response_fail({"msg": "参数不正确"})


# 发送邮箱验证地址
def send_email_verification_link(user):
    from core.models import RegisterConfirm
    from django.core.mail import send_mail
    from PhotoShare.settings import EMAIL_HOST_USER
    from PhotoShare.settings import DOMAIN
    random_str = generate_random()
    verify_link = DOMAIN + '/verify/email?code=' + random_str + '&email=' + user['email']
    RegisterConfirm.objects.update_or_create(email=user.email, defaults={"email_code": random_str})
    # TODO: send email
    html_content = '<p>请点击<a href="' + verify_link + '">链接</a>以完成邮箱验证</p>'
    send_mail(
        'email验证',
        html_content,
        EMAIL_HOST_USER,
        [user['email']],
        fail_silently=False,
    )


# 验证邮箱
def verify_email_action(request):
    from core.models import RegisterConfirm
    if 'email' in request.GET and 'code' in request.POST:
        email = request.GET['email']
        code = request.GET['code']
        if RegisterConfirm.objects.filter(email=email, email_code=code).exists():
            RegisterConfirm.objects.filter(email=email, email_code=code).delete()
            User.objects.filter(email=email).update(status=2)  # 升级未验证用户
            return render(request, 'core/index.html', {"msg": "完成验证"})
        else:
            return render(request, 'core/index.html', {"msg": "验证码错误"})
    else:
        return render(request, 'core/index.html', {"msg": "参数不正确"})


# 生成随机字符串
def generate_random():
    import hashlib
    import random
    string = '{0:%Y-%m-%d %H:%M:%S}'.format(datetime.now()) + str(random.randint(1, 1000000))
    md5 = hashlib.md5(string.encode('utf-8'))
    return md5.hexdigest()


# 登出
@require_login
def logout_action(request):
    request.session.flush()  # 清楚所有session的内容和session的cook
    return response_success(msg={"msg": "您已经退出系统"})


# 新增post和获取posts列表
@http_method_limit(http_methods=['POST', 'GET'])
def posts_action(request):
    if request.method == 'POST':
        if SESSION_USER_KEY not in request.session:
            return response_fail({'msg': "请您先登录"})
        post_form = simplejson.loads(request.body)
        user = request.session[SESSION_USER_KEY]
        user_id = user['id']
        post_form['userId'] = user_id
        post_form['username'] = user['username']
        post_form['avatar'] = user['avatar']
        useless_attrs = ['id', 'dateCreated', 'likeCnt', 'liked', 'commentCnt']
        remove_attributes(post_form, useless_attrs)
        try:
            post = Post(post_form)
            cursor = connection.cursor()
            cursor.execute(
                'UPDATE t_user_post SET post_cnt=post_cnt+1 ,posts=array_append(posts, %s::BIGINT ) WHERE id=%s',
                [post.id, user_id])
            return response_success(msg={'post': model_to_dict(post)})
        except:
            return response_fail(msg={'msg': '操作失败，请重试'})

    if request.method == 'GET':
        offset = request.GET.get("offset", "0")
        limit = request.GET.get("limit", "50")
        try:
            offset = int(offset)
            limit = int(limit)
            if limit > MAX_POST:
                limit = MAX_POST
            if SESSION_USER_KEY in request.session:
                user = request.session[SESSION_USER_KEY]
                if ROLE_POST_ADMIN in user['roles']:
                    post_queryset = Post.objects.filter(). \
                                        values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content',
                                               'status', 'categoryId', 'category', 'likedCnt', 'commentCnt',
                                               'tags').order_by(
                        '-dateCreated')[offset:offset + limit]
                    posts = queryset_to_list(post_queryset)
                    return response_success(msg={'posts': posts})
            post_queryset = Post.objects.filter(status=POST_STATUS_PUBLIC).values('id', 'userId', 'username', 'avatar',
                                                                                  'dateCreated', 'type', 'content',
                                                                                  'status', 'categoryId', 'category',
                                                                                  'likedCnt', 'commentCnt',
                                                                                  'tags').order_by('-dateCreated')[
                            offset:offset + limit]
            posts = queryset_to_list(post_queryset)
            return response_success(msg={'posts': posts})
        except:
            return response_fail(msg={'msg': '获取失败'})
    return response_fail(msg={'msg': '不支持其他方法'})


# 删除属性
def remove_attributes(obj, attributes):
    for attr in attributes:
        if attr in obj:
            del obj[attr]


# 将queryset转换为List
def queryset_to_list(queryset):
    result = []
    for instance in queryset:
        result.append(model_to_dict(instance))
    return result


# 对单个post操作：delete，update，get
@http_method_limit(http_methods=['GET', 'PUT', 'DELETE'])
def post_action(request, id):
    try:
        if request.method == "GET":
            post = Post.objects.get(pk=int(id))
            if post.status != POST_STATUS_PUBLIC:
                if SESSION_USER_KEY in request.session:
                    user = request.session[SESSION_USER_KEY]
                    if ROLE_POST_ADMIN not in user['roles'] and post.userId != user['id']:
                        return response_fail({"msg": "无权获取信息"})
            post = model_to_dict(post)
            return response_success(msg={'post': post})
        if request.method == "PUT":
            if SESSION_USER_KEY not in request.session:
                return response_fail({"msg": "请您先登录"})
            post_form = simplejson.loads(request.body)
            user = request.session[SESSION_USER_KEY]
            Post.objects.filter(id=int(id), userId=user['id']) \
                .update(status=int(post_form['status']), content=post_form['content'], tags=post_form['tags'])
            return response_success(msg={'msg': "操作成功"})
        if request.method == "DELETE":
            if SESSION_USER_KEY not in request.session:
                return response_fail({"msg": "请您先登录"})
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                Post.objects.filter(id=int(id)).update(status=3)
            else:
                Post.objects.filter(id=int(id), userId=user['id']).update(status=3)
            return response_success(msg={'msg': "操作成功"})
    except:
        return response_fail(msg={'msg': "操作失败"})


# like 某个post
@http_method_limit(http_methods=['GET'])
@require_login
def post_like_action(request, id):
    user_id = request.session[SESSION_USER_KEY]['id']
    try:
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE t_user_like_post SET like_cnt=like_cnt+1 ,likes=array_append(likes, %s::BIGINT ) WHERE id=%s',
            [int(id), user_id])
        cursor.execute(
            'UPDATE t_post SET liked_cnt=liked_cnt+1 ,liked=array_append(liked, %s::BIGINT ) WHERE id=%s',
            [user_id, int(id)])
        return response_success(msg={'msg': '操作成功'})
    except:
        return response_fail(msg={'msg': '操作失败'})


# unlike 某个post
@http_method_limit(http_methods=['GET'])
@require_login
def post_unlike_action(request, id):
    user_id = request.session[SESSION_USER_KEY]['id']
    try:
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE t_user_like_post SET like_cnt=like_cnt-1 ,likes=array_remove(likes, %s::BIGINT ) WHERE id=%s',
            [int(id), user_id])
        cursor.execute(
            'UPDATE t_post SET liked_cnt=liked_cnt-1 ,liked=array_remove(liked, %s::BIGINT ) WHERE id=%s',
            [user_id, int(id)])
        return response_success(msg={'msg': '操作成功'})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 获取相似的post
def post_similar_action(request):
    return None


# 获取post的评论
@http_method_limit(http_methods=['GET'])
def post_comments_action(request, id):
    offset = request.GET.get("offset", "0")
    limit = request.GET.get("limit", "50")
    try:
        offset = int(offset)
        limit = int(limit)
        if limit > MAX_COMMENT:
            limit = MAX_COMMENT
        comments = Comment.objects.filter(postId=int(id)).order_by('-dateCreated')[offset:offset + limit]
        comments = queryset_to_list(comments)
        return response_success({'comments': comments})
    except:
        return response_fail(msg={'msg': '获取失败'})


# 新增评论
@http_method_limit(http_methods=['POST'])
@require_login
def comments_action(request):
    try:
        comment_form = simplejson.loads(request.body)
        if 'post_id' not in comment_form:
            return response_fail(msg={'msg': 'post_id不能为空'})
        user = request.session[SESSION_USER_KEY]
        comment = Comment(
            userId=user['id'],
            username=user['username'],
            avatar=user['avatar'],
            content=comment_form['content'],
            postId=int(comment_form['post_id'])
        )
        comment.save()
        return response_success(msg={'comment': model_to_dict(comment)})
    except:
        return response_fail(msg={'msg': '获取失败'})


# 删除评论
@http_method_limit(http_methods=['DELETE'])
@require_login
def comment_action(request, id):
    try:
        user = request.session[SESSION_USER_KEY]
        if ROLE_COMMENT_ADMIN in user['roles']:
            Comment.objects.filter(id=int(id)).delete()
            return response_success(msg={'msg': '操作成功'})
        Comment.objects.filter(id=int(id), userId=user['id']).delete()
        return response_success(msg={'msg': '操作成功'})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 获取某个用户详情
@http_method_limit(http_methods=['GET'])
def user_action(request, id):
    try:
        id = int(id)
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if id == user['id'] or ROLE_USER_ADMIN in user['roles']:
                posts = UserPost.objects.get(pk=id)
                likes = UserLikePost.objects.get(pk=id)
                follows = UserFollow.objects.get(pk=id)
                posts = model_to_dict(posts)
                likes = model_to_dict(likes)
                follows = model_to_dict(follows)
                return response_success({"user": user, "posts": posts, "likes": likes, "follows": follows})
        user = User.objects.get(pk=id)
        user = model_to_dict(user)
        posts = UserPost.objects.get(pk=id)
        posts = model_to_dict(posts)
        result = {'user': user, 'posts': posts}
        try:
            likes = UserLikePost.objects.get(pk=id, status=PUBLIC_CHOICE)
            likes = model_to_dict(likes)
            result['likes'] = likes
        except UserPost.DoesNotExist:
            result['likes'] = {}
        try:
            follows = UserFollow.objects.get(pk=id, status=PUBLIC_CHOICE)
            follows = model_to_dict(follows)
            result['follows'] = follows
        except UserFollow.DoesNotExist:
            result['follows'] = {}
        return response_success(msg=result)
    except:
        return response_fail(msg={'msg': "获取失败"})


# 获取用户关注的列表
@http_method_limit(http_methods=['GET'])
def user_follows_action(request, id):
    try:
        id = int(id)
        form_data = simplejson.loads(request.body)
        follows = form_data['follows']
        if not isinstance(follows, type([])):
            return response_fail(msg={'msg': '参数错误'})
        if len(follows) > MAX_USER:
            return response_fail(msg={'msg': '查询数量过多'})
        users = User.objects.filter(id__in=follows).values('id', 'username', 'avatar')
        users = queryset_to_list(users)
        return response_success(msg={'users': users})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 用户posts列表
@http_method_limit(http_methods=['GET'])
def user_posts_action(request):
    try:
        id = int(id)
        form_data = simplejson.loads(request.body)
        post_id_list = form_data['posts']
        if not isinstance(post_id_list, type([])):
            return response_fail(msg={'msg': '参数错误'})
        if len(post_id_list) > MAX_USER:
            return response_fail(msg={'msg': '查询数量过多'})
        posts = Post.objects.filter(id__in=post_id_list).values('id', 'userId', 'username', 'avatar', 'dateCreated',
                                                                'type', 'content', 'status', 'categoryId', 'category',
                                                                'likedCnt', 'commentCnt', 'tags')
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 搜索用户的posts
@http_method_limit(http_methods=['GET'])
def user_posts_search_action(request, id):
    from django.db.models import Q
    try:
        id = int(id)
        if 'query' not in request.GET:
            return response_fail(msg={'msg': '查询参数不能为空'})
        query = request.GET['query']
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles'] or id == user['id']:
                posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query), Q(id=id)). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query),
                                    Q(status=POST_STATUS_PUBLIC), Q(id=id)). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 关注用户
@http_method_limit(http_methods=['GET'])
@require_login
def user_follow_action(request, id):
    user_id = request.session[SESSION_USER_KEY]['id']
    try:
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE t_user_follow SET follow_cnt=follow_cnt+1 ,follow_who=array_append(follow_who, %s::BIGINT ) WHERE id=%s',
            [user_id, int(id)])
        cursor.execute(
            'UPDATE t_user_follow_by SET followby_cnt=t_user_follow_by.followby_cnt+1 ,who_follow=array_append(who_follow, %s::BIGINT ) WHERE id=%s',
            [user_id, int(id)])
        return response_success(msg={'msg': '操作成功'})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 取消关注用户
@http_method_limit(http_methods=['GET'])
@require_login
def user_unfollow_action(request, id):
    user_id = request.session[SESSION_USER_KEY]['id']
    try:
        cursor = connection.cursor()
        cursor.execute(
            'UPDATE t_user_follow SET follow_cnt=follow_cnt-1 ,follow_who=array_remove(follow_who, %s::BIGINT ) WHERE id=%s',
            [int(id), user_id])
        cursor.execute(
            'UPDATE t_user_follow_by SET followby_cnt=followby_cnt-1 ,who_follow=array_remove(who_follow, %s::BIGINT ) WHERE id=%s',
            [user_id, int(id)])
        return response_success(msg={'msg': '操作成功'})
    except:
        return response_fail(msg={'msg': '操作失败'})


# 查看某个category的posts
@http_method_limit(http_methods=['GET'])
def category_action(request, id):
    try:
        id = int(id)
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                posts = Post.objects.filter(categoryId=id). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(status=POST_STATUS_PUBLIC, categoryId=id). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 查看某个category下推荐的posts
@http_method_limit(http_methods=['GET'])
def category_recommend_action(request, id):
    try:
        id = int(id)
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                posts = Post.objects.filter(categoryId=id). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(status=POST_STATUS_PUBLIC, categoryId=id). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 在category下搜索posts
@http_method_limit(http_methods=['GET'])
def category_search_action(request, id):
    from django.db.models import Q
    try:
        id = int(id)
        if 'query' not in request.GET:
            return response_fail(msg={'msg': '查询参数不能为空'})
        query = request.GET['query']
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query),
                                            Q(categoryId=id)). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query),
                                    Q(status=POST_STATUS_PUBLIC), Q(categoryId=id)). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 全局搜索posts
@http_method_limit(http_methods=['GET'])
def search_posts_action(request):
    from django.db.models import Q
    try:
        if 'query' not in request.GET:
            return response_fail(msg={'msg': '查询参数不能为空'})
        query = request.GET['query']
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_POST_ADMIN in user['roles']:
                posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query)). \
                            values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                                   'categoryId', 'category',
                                   'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
                posts = queryset_to_list(posts)
                return response_success(msg={'posts': posts})
        posts = Post.objects.filter(Q(tags__contains=[query]) | Q(content__title__contains=query)). \
                    values('id', 'userId', 'username', 'avatar', 'dateCreated', 'type', 'content', 'status',
                           'categoryId', 'category',
                           'likedCnt', 'commentCnt', 'tags').order_by('dateCreated')[offset:offset + limit]
        posts = queryset_to_list(posts)
        return response_success(msg={'posts': posts})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 全局搜索users
@http_method_limit(http_methods=['GET'])
def search_users_action(request):
    from django.db.models import Q
    try:
        if 'query' not in request.GET:
            return response_fail(msg={'msg': '查询参数不能为空'})
        query = request.GET['query']
        offset = request.GET.get('offset', 0)
        offset = int(offset)
        limit = request.GET['limit', MAX_POST]
        limit = int(limit)
        if limit > MAX_POST:
            limit = MAX_POST
        if SESSION_USER_KEY in request.session:
            user = request.session[SESSION_USER_KEY]
            if ROLE_USER_ADMIN in user['roles']:
                users = User.objects.filter(Q(tags__contains=[query]) | Q(username=query))[offset:offset + limit]
                users = queryset_to_list(users)
                return response_success(msg={'users': users})
        users = Post.objects.filter(Q(tags__contains=[query]) | Q(username=query))[offset:offset + limit]
        users = queryset_to_list(users)
        return response_success(msg={'users': users})
    except:
        return response_fail(msg={'msg': '查询失败'})


# 上传头像 TODO
@http_method_limit(http_methods=['POST'])
@require_login
def upload_avatar(request):
    if 'avatar' in request.FILES:
        (is_success, result) = handle_avatar(request.FILES['avatar'])
        if not is_success:
            return response_fail(msg=result)
        user = request.session[SESSION_USER_KEY]
        User.objects.filter(id=user['id']).update(avatar=result['id'])
        return response_success(msg=result)
    return response_fail(msg={'msg': '请上传头像文件'})


def handle_avatar(f):
    import pyvips
    from core.settings import AVATAR_SIZE_LARGE, AVATAR_SIZE_NORMAL, AVATAR_SIZE_SMALL, PATH_AVATAR
    if f.size > MAX_AVATAR_SIZE:
        return False, {'msg': '文件过大'}

    if not test_image_suffix(f.name):
        return False, {'msg': '请上传规定图片格式'}
    try:
        image = pyvips.Image.new_from_buffer(f.read(), "")
        id = generate_random()
        small_image = image.smartcrop(AVATAR_SIZE_SMALL, AVATAR_SIZE_SMALL, interesting='centre')
        small_image.webpsave(PATH_AVATAR + id + '_s.webp')
        normal_image = image.smartcrop(AVATAR_SIZE_NORMAL, AVATAR_SIZE_NORMAL, interesting='centre')
        normal_image.webpsave(PATH_AVATAR + id + '.webp')
        large_image = image.smartcrop(AVATAR_SIZE_LARGE, AVATAR_SIZE_LARGE, interesting='centre')
        large_image.webpsave(PATH_AVATAR + id + '_l.webp')
        return True, {'id': id}
    except Exception as e:
        print(e)
    return False, {}


# 检测图片后缀
def test_image_suffix(filename):
    has_image_suffix = False
    if filename.endswith('.jpg') or filename.endswith('.jpeg') \
            or filename.endswith('.webp') or filename.endswith(
        '.png'):
        has_image_suffix = True
    return has_image_suffix


# 上传图片
@http_method_limit(http_methods=['POST'])
@require_login
def upload_image(request):
    if 'images' not in request.FILES:
        return response_fail(msg={'msg': '请上传图片'})
    images = request.FILES.getlist('images')
    image_info_list = []
    for image in images:
        if image.size < MAX_IMAGE_SIZE and test_image_suffix(image.name):
            is_success, image_info = handle_image(image)
            if is_success:
                image_info_list.append(image_info)
    return response_success(msg={'images': image_info_list})


def handle_image(f):
    import pyvips
    try:
        id = generate_random()
        image = pyvips.Image.new_from_buffer(f.read(), "")
        height = image.height
        width = image.width
        ratio = height / width
        scale_small = 1
        if width > IMAGE_SIZE_SMALL:
            scale_small = IMAGE_SIZE_SMALL / width
        small_image = image.resize(scale_small)
        small_image.webpsave(PATH_IMAGE + id + '_s.webp')
        scale_normal = 1
        if width > IMAGE_SIZE_NORMAL:
            scale_normal = IMAGE_SIZE_NORMAL / width
        normal_image = image.resize(scale_normal)
        normal_image.webpsave(PATH_IMAGE + id + '.webp')
        image.webpsave(PATH_IMAGE + id + '_l.webp')
        return True, {'id': id, 'ratio': ratio}
    except Exception as e:
        print(e)
        return False, {}


# 上传视频
@http_method_limit(http_methods=['POST'])
@require_login
def upload_video(request):
    return None


def handle_video(f):
    pass


# 上传文件
@http_method_limit(http_methods=['POST'])
@require_login
def upload_file(request):
    if 'files' not in request.FILES:
        return response_fail(msg={'msg': '请上传文件'})
    files = request.FILES.getlist('files')
    file_info_list = []
    for file in files:
        if file.size < MAX_FILE_SIZE:
            is_success, file_info = handle_file(file)
            if is_success:
                file_info_list.append(file_info)
    return response_success(msg={'files': file_info_list})


def handle_file(f):
    try:
        temp_list = f.name.split('.')
        if len(temp_list) > 1:
            id = generate_random()
            name = f.name.replace(temp_list[0], id)
            with open(PATH_FILE + name, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            return True, {'name': name}
        return False, {}
    except:
        return False, {}


# 文件上传的过滤器
def upload_filter(name, size=1000 * 1024 * 1024, allow_suffix=[]):
    def handle_func(method):
        def new_method(request, *args, **kw):
            if name not in request.FILES:
                return response_fail(msg={'msg': "请上传文件"})
            files = request.FILES.getlist(name)
            for file in files:
                if file.size > size:
                    return response_fail(msg={'msg': "上传文件超出限制"})
                if len(allow_suffix) > 0:
                    temps = file.name.split('.')
                    temp_len = len(temps)
                    if temp_len > 1:
                        suffix = temps[temp_len - 1]
                        if suffix not in allow_suffix:
                            return response_fail(msg={'msg': "不能上传非法文件"})
            return method(request, *args, **kw)

        return new_method

    return handle_func


# 检测是否请求JSON
def is_request_json(request):
    content_type = request.content_type
    if content_type.endswith("json"):
        return True
    return False
