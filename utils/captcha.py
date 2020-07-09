#coding:utf8 -*-
import random
from PIL import Image,ImageDraw,ImageFont,ImageFilter

numbers = ''.join(map(str,range(10)))
chars = ''.join(numbers)

def create_validate_code(
        size=(120,30),
        chars = chars,
        mode = 'RGB',
        bg_color = (255,255,255),
        fg_color = (255,0,0),
        font_size = 18,
        font_type = 'STZHONGS.TTF',
        length = 4,
        draw_points = True,
        point_chance = 2):
    width,height = size
    img = Image.new(mode,size,bg_color)
    draw = ImageDraw.Draw(img)

    #生成给定长度的字符串
    def get_chars():
        return random.sample(chars,length)

    #绘制干扰点
    def create_points():
        chance = min(50,max(0,int(point_chance)))
        for w in range(width):
            for h in range(height):
                tmp = random.randint(0,50)
                if tmp > 50 - chance:
                    draw.point((w,h),fill=(0,0,0))

    #绘制验证码字符
    def create_str():
        c_chars = get_chars()
        strs = '%s' % ''.join(c_chars)
        font = ImageFont.truetype(font_type,font_size)
        font_width,font_height = font.getsize(strs)
        draw.text(((width - font_width) / 3,(height - font_height) / 4),strs,font=font,fill=fg_color)
        return strs
    if draw_points:
        create_points()
    strs = create_str()
    #图形扭曲参数
    params = [1 - float(random.randint(1,2)) / 100,
              0,
              0,
              0,
              1 - float(random.randint(1,10)) / 100,
              float(random.randint(1,2)) / 500,
              0.001,
              float(random.randint(1,2)) / 500
              ]
    img = img.transform(size,Image.PERSPECTIVE,params)
    img = img.filter(ImageFilter.EDGE_ENHANCE_MORE)
    return img,strs