from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models

# Comment
from django.utils import timezone


class Comment(models.Model):
    id = models.BigAutoField('ID', db_column='id', primary_key=True)
    dateCreated = models.DateTimeField('创建日期', db_column='date_created', default=timezone.now)
    userId = models.BigIntegerField('用户ID', db_column='user_id')
    username = models.CharField('用户名', db_column='username', max_length=30)
    avatar = models.CharField('头像', db_column='avatar', max_length=50)
    content = JSONField('评论内容', db_column='content')
    postId = models.BigIntegerField('post ID', db_column='post_id')

    class Meta:
        db_table = 't_comment'
        verbose_name = '评论'
        verbose_name_plural = '评论'


POST_TYPE_CHOICES = (
    (1, '文本'),
    (2, '图片'),
    (3, '视频'),
    (4, '调查'),
    (5, '其他'),
)
POST_STATUS_PUBLIC = 1
POST_STATUS_PRIVATE = 2
POST_STATUS_DELETED = 3
POST_STATUS_CHOICES = (
    (POST_STATUS_PUBLIC, '公开'),
    (POST_STATUS_PRIVATE, '私人'),
    (POST_STATUS_DELETED, '已删除'),
)


# Post
class Post(models.Model):
    id = models.BigAutoField('ID', db_column='id', primary_key=True)
    userId = models.BigIntegerField('用户ID', db_column='user_id')
    username = models.CharField('用户名', db_column='username', max_length=50)
    avatar = models.CharField('头像', db_column='avatar', max_length=50)
    dateCreated = models.DateTimeField('创建日期', db_column='date_created', default=timezone.now)
    type = models.SmallIntegerField('类型', db_column='type', choices=POST_TYPE_CHOICES, default=2)
    content = JSONField('详情', db_column='content', default={})
    status = models.SmallIntegerField('状态', db_column='status', choices=POST_STATUS_CHOICES, default=1)
    categoryId = models.SmallIntegerField('所属类别ID', db_column='category_id', blank=True, null=True)
    category = models.CharField('所属类别', db_column='category', max_length=30, blank=True, null=True)
    likedCnt = models.BigIntegerField('点赞的数量', db_column='liked_cnt', default=0)
    liked = ArrayField(models.BigIntegerField('点过赞的用户'), db_column='liked', verbose_name='点赞的数量', default=[])
    commentCnt = models.BigIntegerField('评论数量', db_column='comment_cnt', default=0)
    tags = ArrayField(models.TextField('标签', max_length=20), db_column='tag_list', default=[])

    class Meta:
        db_table = 't_post'
        verbose_name = '帖子'
        verbose_name_plural = '帖子'


class User(models.Model):
    USER_STATUS_CHOICES = (
        (1, '活跃'),
        (2, '不活跃'),
        (3, '冻结'),
        (4, '未激活'),
    )
    id = models.BigAutoField('ID', db_column='id', primary_key=True)
    username = models.CharField('用户名', db_column='username', max_length=30)
    email = models.CharField('EMAIL', db_column='email', max_length=30, blank=True, null=True)
    phone = models.CharField('电话', db_column='phone', max_length=20, blank=True, null=True)
    avatar = models.CharField('头像', db_column='avatar', max_length=50)
    password = models.CharField('密码', db_column='password', max_length=50)
    dateRegister = models.DateTimeField('注册日期', db_column='date_register', default=timezone.now)
    lastLogin = models.DateTimeField('最近登录日期', db_column='last_login', default=timezone.now)
    roles = ArrayField(models.BigIntegerField('用户角色ID'), db_column='role_list', default=[])
    tags = ArrayField(models.TextField('标签', max_length=20), db_column='tag_list', default=[])
    profile = JSONField('用户资料', db_column='profile', blank=True, null=True, default={})
    status = models.SmallIntegerField('用户状态', db_column='status', choices=USER_STATUS_CHOICES, default=4)

    class Meta:
        db_table = 't_user'
        verbose_name = '用户'
        verbose_name_plural = '用户'


PUBLIC_CHOICE = 1
PRIVATE_CHOICE = 2

PUBLIC_CHOICES = (
    (PUBLIC_CHOICE, '公开'),
    (PRIVATE_CHOICE, '私人'),
)


class UserFollow(models.Model):
    id = models.BigIntegerField('用户ID', db_column='id', primary_key=True)
    followWho = ArrayField(models.BigIntegerField('用户ID'), db_column='follow_who', verbose_name='关注的用户',
                           default=[])
    followCnt = models.BigIntegerField('用户关注的总数', db_column='follow_cnt', default=0)
    status = models.SmallIntegerField('状态', db_column='status', choices=PUBLIC_CHOICES, default=1)

    class Meta:
        db_table = 't_user_follow'
        verbose_name = '用户关注的人'
        verbose_name_plural = '用户关注的人'


class UserFollowBy(models.Model):
    id = models.BigIntegerField('用户ID', db_column='id', primary_key=True)
    whoFollow = ArrayField(models.BigIntegerField('用户ID'), db_column='who_follow', verbose_name='关注你的用户', blank=True,
                           null=True)
    followByCnt = models.BigIntegerField('用户关注的总数', db_column='followby_cnt', default=0)

    class Meta:
        db_table = 't_user_follow_by'
        verbose_name = '关注用户的人'
        verbose_name_plural = '关注用户的人'


class UserLikePost(models.Model):
    id = models.BigIntegerField('用户ID', db_column='id', primary_key=True)
    likes = ArrayField(models.BigIntegerField('贴子ID'), db_column='likes', verbose_name='喜欢的posts', default=[])
    likeCnt = models.BigIntegerField('用户喜欢的帖子总数', db_column='like_cnt', default=0)
    status = models.SmallIntegerField('状态', db_column='status', choices=PUBLIC_CHOICES, default=1)

    class Meta:
        db_table = 't_user_like_post'
        verbose_name = '用户喜欢的帖子'
        verbose_name_plural = '用户喜欢的帖子'


class UserPost(models.Model):
    id = models.BigIntegerField('用户ID', db_column='id', primary_key=True)
    posts = ArrayField(models.BigIntegerField('贴子ID'), db_column='posts', verbose_name='发布的帖子', default=[])
    postCnt = models.BigIntegerField('用户发布的帖子总数', db_column='post_cnt', default=0)

    class Meta:
        db_table = 't_user_post'
        verbose_name = '用户发布的帖子'
        verbose_name_plural = '用户发布的帖子'


class Category(models.Model):
    id = models.AutoField('分类ID', db_column='id', primary_key=True)
    name = models.CharField('分类名称', db_column='name', max_length=20, unique=True)

    class Meta:
        db_table = 't_category'
        verbose_name = '分类'
        verbose_name_plural = '分类'


class RegisterConfirm(models.Model):
    id = models.AutoField("注册验证ID", db_column='id', primary_key=True)
    email = models.CharField('邮箱', db_column='email', max_length=30, null=True, blank=True)
    email_code = models.CharField('邮箱验证码', db_column='email_code', max_length=30, null=True, blank=True)
    phone = models.CharField('电话', db_column='phone', max_length=30, null=True, blank=True)
    phone_code = models.CharField('电话验证码', db_column='phone_code', max_length=30, null=True, blank=True)
    phone_order_id = models.CharField('电话验证订单编号', db_column='phone_order_id', max_length=30, null=True, blank=True)

    class Meta:
        db_table = 't_regconfirm'
        verbose_name = '注册验证'
        verbose_name_plural = '注册验证'
