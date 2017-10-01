from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index_action, name='index'),  # 主页
    url(r'^login$', views.login_action, name='login'),  # 登录
    url(r'^register$', views.register_action, name='register'),  # 注册
    url(r'^logout$', views.logout_action, name='logout'),  # 登出
    url(r'^verify/email$', views.verify_email_action, name='verify_email'),  # 验证邮箱
    url(r'^verify/phone$', views.verify_phone_action, name='verify_phone'),  # 验证电话
    url(r'^verify/send_phone_code$', views.send_phone_verification_code_action, name='send_phone_verification_code'),
    # 发送手机验证码

    url(r'^posts$', views.posts_action, name='posts'),  # 新增post和获取posts列表
    url(r'^posts/(?P<id>[0-9]+)$', views.post_action, name='post_action'),  # 对单个post操作：delete，update，get
    url(r'^posts/(?P<id>[0-9]+)/like$', views.post_like_action, name='post_like'),  # like 某个post
    url(r'^posts/(?P<id>[0-9]+)/unlike$', views.post_unlike_action, name='post_unlike'),  # unlike 某个post
    url(r'^posts/(?P<id>[0-9]+)/similar$', views.post_similar_action, name='post_similar'),  # 获取相似的post
    url(r'^posts/(?P<id>[0-9]+)/comments$', views.post_comments_action, name='post_comments'),  # 获取post的评论
    url(r'^comments$', views.comments_action, name='comments'),  # 新增评论
    url(r'^comments/(?P<id>[0-9]+)$', views.comment_action, name='comments_action'),  # 删除评论

    url(r'^users/(?P<id>[0-9]+)$', views.user_action, name='user_action'),  # 获取某个用户详情
    url(r'^users/(?P<id>[0-9]+)/follows$', views.user_follows_action, name='user_follows'),  # 获取用户关注的列表
    url(r'^users/(?P<id>[0-9]+)/posts$', views.user_posts_action, name='user_posts'),  # 用户posts列表
    url(r'^users/(?P<id>[0-9]+)/posts/search$', views.user_posts_search_action, name='user_posts_search'),  # 搜索用户的posts
    url(r'^users/(?P<id>[0-9]+)/follow$', views.user_follow_action, name='user_follow'),  # 关注用户
    url(r'^users/(?P<id>[0-9]+)/unfollow$', views.user_unfollow_action, name='user_unfollow'),  # 取消关注用户

    url(r'^categroy/(?P<id>[0-9]+)$', views.category_action, name='category'),  # 查看某个category的posts
    url(r'^categroy/(?P<id>[0-9]+)/recommend$', views.category_recommend_action, name='category_recommend'),
    # 查看某个category下推荐的posts
    url(r'^categroy/(?P<id>[0-9]+)/search', views.category_search_action, name='category_search'),  # 在category下搜索posts

    url(r'^search/posts', views.search_posts_action, name='search_posts'),  # 全局搜索posts
    url(r'^search/users', views.search_users_action, name='search_users'),  # 全局搜索users

    url(r'^upload/avatar$',views.upload_avatar,name='upload_avatar'),
    url(r'^upload/image$',views.upload_image,name='upload_image'),
    url(r'^upload/media$', views.upload_video, name='upload_media'),
    url(r'^upload/file$',views.upload_file,name='upload_file'),
]
