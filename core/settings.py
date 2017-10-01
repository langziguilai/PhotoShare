# 配置文件
from datetime import timedelta

SESSION_USER_KEY = 'USER'  # 在session中保存用户信息
SESSION_TIME_CAN_NEXT_LOGIN = "next_login_time"  # 在session中保存用户下次准许登录时间
SESSION_LOGIN_FAIL_CNT = 'login_fail_cnt'  # 登录失败的次数
MAX_LOGIN_TIMES = 10
LOGIN_FORBIDDEN_DURATION = timedelta(minutes=15)

CODE_SUCCESS = 1
CODE_FAIL = 0

# 权限
ROLE_COMMENT_ADMIN = 1
ROLE_POST_ADMIN = 2
ROLE_USER_ADMIN = 3

# 最多获取
MAX_POST = 100
MAX_COMMENT = 100
MAX_USER = 100

# 上传文件路径
PATH_AVATAR = '/Users/langziguilai/PycharmProjects/PhotoShare/PhotoShare/core/static/resource/avatar/'
MAX_AVATAR_SIZE = 1024 * 1024  # 最大1m
AVATAR_SIZE_LARGE = 120
AVATAR_SIZE_NORMAL = 80
AVATAR_SIZE_SMALL = 40

PATH_IMAGE = '/Users/langziguilai/PycharmProjects/PhotoShare/PhotoShare/core/static/resource/image/'
MAX_IMAGE_SIZE = 20 * 1024 * 1024  # 最大20m
IMAGE_SIZE_SMALL = 277
IMAGE_SIZE_NORMAL = 540
PATH_VIDEO = '/Users/langziguilai/PycharmProjects/PhotoShare/PhotoShare/core/static/resource/video/'
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 最大100m
PATH_FILE = '/Users/langziguilai/PycharmProjects/PhotoShare/PhotoShare/core/static/resource/file/'
MAX_FILE_SIZE = 50 * 1024 * 1024  # 最大50m
