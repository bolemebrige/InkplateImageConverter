import os
import hashlib
import requests
from flask import Flask,flash, request, redirect, url_for,request,render_template,send_from_directory, session,send_file

from werkzeug.utils import secure_filename
from PIL import Image,ImageFilter,ImageEnhance
#local



app = Flask(__name__)

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/inkplate')
def index():
    return render_template('inkplate.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

@app.route('/inkplate/form', methods=['POST'])
def form():
    if request.method == 'POST':

        version=request.form.get('version')
        algorithm=request.form.get('algorithm')
                # check if the post request has the file part
        if 'picture' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['picture']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            pic_resource=url_for('uploaded_file',
                                    filename=filename)
            if(algorithm=='Dithering'):

                return dithering_transform(pic_resource)
            elif(algorithm == 'Grayscale'):
                return grayscale_transform(pic_resource)
            elif(algorithm == 'Black and White'):
                return bw_transform(pic_resource)


@app.route('/inkplate/preview/<filename>/<size>')
def preview(filename,size):
    path="static/arrays/"+filename[0:-4]+".h"
    file="processed/"+filename
    download_link=str("/inkplate/download/"+filename[0:-4]+".h")
    print file
    h_file = open(path, "r")
    c_array=h_file.read()
    h_file.close()
    return render_template('preview.html',pic_resource=file,c_array=c_array,size=size,download_file=download_link)

@app.route('/inkplate/preview/error')
def show_error():
    return render_template('error.html')


@app.route('/inkplate/download/<header_file>')
def return_file(header_file):
    header_path="static/arrays/"+header_file
    print header_path
    try:
        return send_file(header_path, attachment_filename=header_file)
    except Exception as e:
        return str(e)



def dithering_transform(picture):
    path='.'+picture
    splitted=path.split('/')
    name=splitted[-1:]
    print name[0]
    name=str(name[0])
    name_splitted=name.split('.')
    out_name='dither_'+str(name_splitted[0])+'.bmp'
    new_img = Image.open(path)
    size_tuple=check_size(new_img.width,new_img.height)
    new_img_resized=new_img.resize(size_tuple)
    dither_img = new_img_resized.convert(mode="1", matrix=None, palette=0, colors=256)
    dither_img.save('static/processed/'+out_name)
    #promjeni da se ne sprema slika bzvz ako moze
    c_array=craft_array_dither('static/processed/'+out_name)
    c_array_size=len(c_array)
    c_array=str(c_array)
    c_array=c_array.strip('[]')
    c_array_file_path="static/arrays/"+'dither_'+str(name_splitted[0])+".h"

    c_array_format=c_array.replace("'","")
    c_array_format="{"+c_array_format+"}"
    h_file = open(c_array_file_path, "w")
    h_file.write("const uint8_t {0} PROGMEM[{1}]={2}".format(out_name,c_array_size,c_array_format))
    h_file.close()
    redirect_link='/inkplate/preview/'+out_name+'/'+ str(size_tuple)

    return redirect(redirect_link)


def grayscale_transform(picture):
    path='.'+picture
    splitted=path.split('/')
    name=splitted[-1:]
    print name[0]
    name=str(name[0])
    name_splitted=name.split('.')
    out_name='grayscale_'+str(name_splitted[0])+'.bmp'
    new_img = Image.open(path)
    size_tuple=check_size(new_img.width,new_img.height)
    new_img_resized=new_img.resize(size_tuple)
    grayscale_img = new_img_resized.convert(mode="L", matrix=None, palette=0, colors=256)
    grayscale_img=gamma_correction(grayscale_img)

    grayscale_img.save('static/processed/'+out_name)

    redirect_link='/inkplate/preview/'+out_name+'/'+ str(size_tuple)

    c_array=craft_array_grayscale('static/processed/'+out_name)
    c_array_size=len(c_array)
    c_array=str(c_array)
    c_array=c_array.strip('[]')
    c_array_file_path="static/arrays/"+'grayscale_'+str(name_splitted[0])+".h"
    c_array_format=c_array.replace("'","")
    c_array_format="{"+c_array_format+"}"
    h_file = open(c_array_file_path, "w")
    h_file.write("const uint8_t {0} PROGMEM[{1}]={2}".format(out_name,c_array_size,c_array_format))
    h_file.close()
    return redirect(redirect_link)

def bw_transform(picture):
    path='.'+picture
    splitted=path.split('/')
    name=splitted[-1:]
    print name[0]
    name=str(name[0])
    name_splitted=name.split('.')
    out_name='b&w_'+str(name_splitted[0])+'.bmp'
    new_img = Image.open(path)
    size_tuple=check_size(new_img.width,new_img.height)
    new_img_resized=new_img.resize(size_tuple)
    thresh = 128
    fn = lambda x : 255 if x > thresh else 0
    bw_image = new_img_resized.convert('L').point(fn, mode='1')

    bw_image.save('static/processed/'+out_name)

    c_array=craft_array_dither('static/processed/'+out_name)
    c_array_size=len(c_array)
    c_array=str(c_array)
    c_array=c_array.strip('[]')
    c_array_file_path="static/arrays/"+'b&w_'+str(name_splitted[0])+".h"

    c_array_format=c_array.replace("'","")
    c_array_format="{"+c_array_format+"}"
    h_file = open(c_array_file_path, "w")
    h_file.write("const uint8_t {0} PROGMEM[{1}]={2}".format(out_name,c_array_size,c_array_format))
    h_file.close()
    redirect_link='/inkplate/preview/'+out_name+'/'+ str(size_tuple)

    return redirect(redirect_link)



def check_size(width,height):
    if(width<7680):
        if(width>800):
            k_width=800/float(width)
            new_width=width*k_width
            new_height=height*k_width

        elif(height>600):
            k_height=600/float(height)
            new_width=width*k_height
            new_height=height*k_height
        else:
            new_width=width
            new_height=height
        return_value=(int(new_width),int(new_height))
        return return_value
    else:
        return redirect('/inkplate/preview/error')



def craft_array_dither(path):
    Img = Image.open(path)
    x=0
    y=0

    c_array=[]
    for y in range(Img.height):
        bit_counter=1
        for x in range(Img.width):
            bit_counter+=1
            coordinate=(x,y)
            pixel_value=Img.getpixel(coordinate)

            if(pixel_value == 0):
                pixel_value=1
            else:
                pixel_value=0

            if 'byte' in vars():

                byte += str(pixel_value)
            else:

                byte=str(pixel_value)

            if(bit_counter%8 == 0):
                hex_byte=hex(int(byte, 2))


                c_array.append(hex_byte)

                del byte
            elif(y == Img.width-1):
                hex_byte=hex(int(byte, 2))
                c_array.append(hex_byte)

                del byte

    #c_array_str=''.join(c_array)
    if(y==Img.height-1):
        return c_array


def craft_array_grayscale(path):
    Img = Image.open(path)
    x=0
    y=0

    c_array=[]
    for y in range(Img.height):
        bit_counter=1
        for x in range(Img.width):

            coordinate=(x,y)
            pixel_value=Img.getpixel(coordinate)


            if(pixel_value < 64):
                scaled_gs_value='000'
            elif(pixel_value>=64 and pixel_value<127):

                scaled_gs_value='001'
            elif(pixel_value>=127 and pixel_value<159):

                scaled_gs_value='010'
            elif(pixel_value>=159 and pixel_value<191):

                scaled_gs_value='011'
            elif(pixel_value>=191 and pixel_value<207):

                scaled_gs_value='100'
            elif(pixel_value>=207 and pixel_value<223):

                scaled_gs_value='101'

            elif(pixel_value>=223 and pixel_value<239):

                scaled_gs_value='110'
            elif(pixel_value>=239):

                scaled_gs_value='111'

            if 'byte' in vars():
                #print pixel_value
                byte = byte+ '0' +str(scaled_gs_value) +'0'

                bit_counter+=4
                print bit_counter
            else:
                #print pixel_value
                byte=str(scaled_gs_value)

                bit_counter+=3
                print 'ulazi'

            if(bit_counter == 8):
                hex_byte=hex(int(byte, 2))
                bit_counter=1
                c_array.append(hex_byte)
                del byte
            elif(y == Img.width-1):
                if(len(byte)==3):
                    byte+='00000'
                hex_byte=hex(int(byte, 2))
                bit_counter=1
                c_array.append(hex_byte)
                #print byte
                del byte

    #c_array_str=''.join(c_array)
    if(y==Img.height-1):
        return c_array


def gamma_correction(img):
    #img=Image.open(img_path)
    x=0
    y=0
    gamma = 1.4
    result_img = Image.new("L", (img.width, img.height))
    for y in range(img.height):
        for x in range(img.width):
            coordinate=(x,y)
            pixel_value=float(img.getpixel(coordinate))

            value =255*pow((pixel_value/255),(1/gamma))
            print value
            if value >= 255 :
                value = 255
            result_img.putpixel(coordinate, int(value))
#    result_img.filter(ImageFilter.MedianFilter(7))
    return result_img

def contrast(img):
    BrightnessEnhancer = ImageEnhance.Brightness(img)
    BrightnedImg=BrightnessEnhancer.enhance(1.3)
#napravi sharpness
    ContrastEnhancer = ImageEnhance.Contrast(BrightnedImg)
    enhanced_im = ContrastEnhancer.enhance(1.3)



    return enhanced_im
