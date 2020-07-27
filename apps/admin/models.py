#coding:utf8 -*-
from werkzeug.security import generate_password_hash,check_password_hash
from exts import db
from datetime import datetime

class Users(db.Model):
    __table_name__ = 'users'
    uid = db.Column(db.Integer,primary_key=True,autoincrement=True)
    username = db.Column(db.String(50),nullable=False)
    password = db.Column(db.String(100),nullable=False)
    _password = db.Column(db.String(100),nullable=False)
    email = db.Column(db.String(100),nullable=False,unique=True)
    sex = db.Column(db.String(10),default=0)
    telephone = db.Column(db.String(11))
    status = db.Column(db.Integer)
    is_super = db.Column(db.SmallInteger)
    role_id = db.Column(db.Integer,db.ForeignKey('jq_role.id'))
    remarks = db.Column(db.String(100))
    reg_time = db.Column(db.DateTime, default=datetime.now)
    articles = db.relationship('Articles',lazy = 'dynamic')
    __table_args__ = {
        'mysql_charset': 'utf8',
        'extend_existing': True
    }
    def __init__(self,username,password,email,sex,telephone,remarks,role_id,status):
        self.username = username
        self.password = password
        self.email = email
        self.sex = sex
        self.telephone = telephone
        self.remarks = remarks
        self.role_id = role_id
        self.status = status

    @property
    def password(self):
        return self._password
    @password.setter
    def password(self,raw_password):
        self._password = generate_password_hash(raw_password)
    def check_password(self,raw_password):
        result = check_password_hash(self._password,raw_password)
        return result

#定义文章分类开始
class Articles_Cat(db.Model):
    __tablename__='jq_article_category'
    cat_id=db.Column(db.Integer,primary_key=True,autoincrement=True)#分类ID
    parent_id=db.Column(db.Integer,nullable=False)#分类父ID,父ID不能为空
    cat_name=db.Column(db.String(20),nullable=False)#栏目名称
    keywords=db.Column(db.String(20),nullable=False)#栏目关键字
    description=db.Column(db.Text,nullable=True)#栏目描述可以为空
    cat_sort=db.Column(db.Integer,nullable=True)#栏目排序
    # template=db.Column(db.String(80),nullable=False)# 栏目模板
    status=db.Column(db.Integer,nullable=False)#显示还是隐藏
    dir=db.Column(db.String(80),nullable=False)#如果实现静态化，该栏目的保存路径
    articles = db.relationship("Articles", lazy="dynamic")#一个分类对应多个文章
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
#建立文章和标签的关联表
article_tag = db.Table('article_tag',
                       db.Column('jq_article.aid',db.Integer,db.ForeignKey('jq_article.aid'),primary_key=True),
                       db.Column('jq_tag.tid',db.Integer,db.ForeignKey('jq_tag.tid'),primary_key=True))
#定义文章开始
class Articles(db.Model):
    __tablename__ = 'jq_article'
    aid = db.Column(db.Integer,primary_key=True,autoincrement=True)  #文章ID
    cat_id = db.Column(db.Integer, db.ForeignKey("jq_article_category.cat_id"))  #分类ID
    title = db.Column(db.String(255), nullable=False)  #文章标题,nullable=false是这个字段在保存时必需有值
    shorttitle=db.Column(db.String(255),nullable=True) #短标题可以为空
    source = db.Column(db.String(64), nullable=False)  #文章来源
    keywords=db.Column(db.String(64),nullable=False) #关键字不能为空
    description = db.Column(db.String(512), nullable=False)  #文章摘要
    body = db.Column(db.Text, nullable=False)  #文章内容
    clicks = db.Column(db.Integer, default=0)  #浏览量
    picture = db.Column(db.String(255))  # 文章列表图片路径
    author_id = db.Column(db.Integer, db.ForeignKey("users.uid"))  #当前文章的作者id
    allowcomments=db.Column(db.Integer,default=0) #是否允许评论
    status = db.Column(db.Integer, default=0)  #当前文章状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    create_time=db.Column(db.DateTime,default=datetime.now) #文章添加时间
    is_delete=db.Column(db.Boolean,default=0) #删除标志
    flag=db.Column(db.Boolean,default=0)
    tags = db.relationship('Articles_Tag', secondary=article_tag, backref=db.backref('articles'))
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
#定义文章标签
class Articles_Tag(db.Model):
     __tablename__ = 'jq_tag'
     tid = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 分类ID
     aid = db.Column(db.Integer)  # 外键,文章ID
     cat_id=db.Column(db.SmallInteger)#属于哪个文章栏目下的tag
     tag = db.Column(db.String(40), nullable=False)  # 文章标签,nullable=false是这个字段在保存时必需有值
     add_time=db.Column(db.DateTime,default=datetime.now)
     __table_args__ = {
         'mysql_charset': 'utf8'
     }
#评论
class Comment(db.Model):
    __tablename__='jq_comment'
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    aid=db.Column(db.Integer)#外键，文章ID
    title=db.Column(db.String(255))#评论的文章标题
    user_id=db.Column(db.Integer)#用户ID
    user_name=db.Column(db.String(200))#用户名
    comment=db.Column(db.Text)#评论内容
    status = db.Column(db.Integer, default=0)  # 当前评论状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    parent_id=db.Column(db.Integer)#评论的父ID
    comment_ip=db.Column(db.String(255))#评论者的IP地址
    add_time=db.Column(db.DateTime,default=datetime.now)#评论添加时间
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
#操作日志
class Operate_Log(db.Model):
    __tablename__ = "jq_oplog"  #定义表名
    id = db.Column(db.Integer,primary_key=True) #编号
    #定义外键 db.ForeignKey
    admin_id = db.Column(db.Integer,db.ForeignKey('users.uid')) #所属管理员
    ip = db.Column(db.String(100))  #登录IP
    operate = db.Column(db.String(600))  #操作行为
    add_time = db.Column(db.DateTime,index=True,default=datetime.now) #登录时间 ，默认时间
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
#管理员登录日志
class Admin_Log(db.Model):
    __tablename__ = "jq_adminlog"  #定义表名
    id = db.Column(db.Integer,primary_key=True) #编号
    #定义外键 db.ForeignKey
    admin_id = db.Column(db.Integer,db.ForeignKey('users.uid')) #所属管理员
    operate = db.Column(db.String(300))  # 操作行为
    ip = db.Column(db.String(100))  #登录IP
    time = db.Column(db.String(100))#时间戳
    add_time = db.Column(db.DateTime,index=True,default=datetime.now) #登录时间 ，默认时间
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
# 定义权限数据模型
class Auth(db.Model):
    __tablename__ = "jq_auth"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100))  # 名称，不能重复
    url = db.Column(db.String(255))  # 地址
    parent_id=db.Column(db.Integer,default=0)#父ID,不能为空
    status=db.Column(db.Integer, default=0)#0允许显示，-1表示不显示
    add_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 添加时间
    __table_args__ = {
        'mysql_charset': 'utf8'
    }
# 定义角色数据模型
class Role(db.Model):
    __tablename__ = "jq_role"
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 名称
    description=db.Column(db.String(600))#角色描述
    auths = db.Column(db.String(600)) # 权限列表
    add_time = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 添加时间
    admins=db.relationship("Users",backref='jq_role')
    __table_args__ = {
        'mysql_charset': 'utf8'
    }