from django.contrib import admin

# Register your models here.
from django.contrib.admin import models

from .models import User, Post, Comment, UserFollow, UserFollowBy, UserLikePost, UserPost, Category


class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'phone')  # 列表展示属性
    list_filter = ('dateRegister',)  # 过滤器


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'userId', 'username',)  # 列表展示属性
    list_filter = ('dateCreated',)  # 过滤器


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'userId', 'username',)  # 列表展示属性
    list_filter = ('dateCreated',)  # 过滤器


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name',)  # 列表展示属性
    search_fields = ['name']  # 搜索


class UserFollowAdmin(admin.ModelAdmin):
    list_display = ('id', 'followCnt',)  # 列表展示属性
    search_fields = ['followCnt']  # 搜索


class UserFollowByAdmin(admin.ModelAdmin):
    list_display = ('id', 'followByCnt',)  # 列表展示属性
    search_fields = ['followByCnt']  # 搜索


class UserLikePostAdmin(admin.ModelAdmin):
    list_display = ('id', 'likeCnt',)  # 列表展示属性
    search_fields = ['likeCnt']  # 搜索


class UserPostAdmin(admin.ModelAdmin):
    list_display = ('id', 'postCnt',)  # 列表展示属性
    search_fields = ['postCnt']  # 搜索


admin.site.register(User, UserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(UserFollow, UserFollowAdmin)
admin.site.register(UserFollowBy, UserFollowByAdmin)
admin.site.register(UserLikePost, UserLikePostAdmin)
admin.site.register(UserPost, UserPostAdmin)
admin.site.register(Category, CategoryAdmin)
