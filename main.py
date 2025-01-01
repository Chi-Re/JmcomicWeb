from io import BytesIO

from flask import Flask, request, send_file, render_template
from jmcomic import *

app = Flask(__name__)

client: JmApiClient = JmOption.default().build_jm_client(domain_list=JmModuleConfig.DOMAIN_API_LIST)
# client.login("", "")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/photo/<photo_id>")
def photo(photo_id: int):
    photo = client.get_photo_detail(photo_id, False)

    return_photos = []

    for p in photo:
        return_photos.append(f"/photo/get_photos?url={p.img_url}")

    return render_template("photo.html", photos=return_photos)


@app.route("/album/<photo_id>")
def album(photo_id: int):
    photo_text = client.req_api("/album", params={
        "id": photo_id
    }).res_data

    photo_content = {
        "id": photo_id,
        "title": photo_text['name'],
        "description": photo_text['description'],
        "cover": f"https://{client.domain_list[0]}/media/albums/{photo_id}.jpg",
        "author": photo_text['author'],  # 作者
        "genre": photo_text['tags'],  # 标签
        "page_count": len(photo_text['images'])  # 页数
    }

    # photo_text = client.get_album_detail(photo_id)
    #
    # photo_content = {
    #     "id": photo_id,
    #     "title": photo_text.name,
    #     # "description": photo_text['description'],
    #     "cover": f"https://{client.domain_list[0]}/media/albums/{photo_id}.jpg",
    #     "author": photo_text.authors,  # 作者
    #     "genre": photo_text.tags,  # 标签
    #     "page_count": int(photo_text.page_count)  # 页数
    # }

    return render_template("album.html", photo_content=photo_content)


@app.route("/media/photos/<photo_id>/<photo_i>.webp")
def media(photo_id: int):
    return photo_id


@app.route("/search/photos", methods=['POST', "GET"])
def search():
    # request.values.get('search')

    if "page" in request.values:
        page: int = int(request.values.get("page"))
    else:
        page: int = 1

    search_txt = request.values.get('search')

    photo_list = get_search_photo(search_txt, page)

    return render_template("search.html", photos=photo_list, page=page, search=search_txt, url='/search/photos')


@app.route("/favorites", methods=['POST', "GET"])
def favorites():
    if "page" in request.values:
        page: int = int(request.values.get("page"))
    else:
        page: int = 1

    try:
        photo_list = get_favorites_photo(page)

    except ResponseUnexpectedException:
        return "您还未登陆"
    except:
        return "∑(っ°Д°;)っ卧槽，报错了"

    return render_template("search.html", photos=photo_list, page=page, url='/favorites')


@app.route("/photo/get_photos", methods=['POST', "GET"])
def get_photos():
    url = request.values.get('url')

    img_byte = decode_and_decode(client, url)

    try:
        img_byte = img_byte.getvalue()
    except AttributeError:
        img_byte = img_byte

    return send_file(BytesIO(img_byte), mimetype="image/webp")


@app.route("/test", methods=['POST', "GET"])
def post_test():
    username = request.values.get('username')
    return username


def get_search_photo(tag: str, page: int) -> List[dict]:
    photos_title_id_list = []

    for i in client.search_site(tag, page):
        print(i)
        photos_title_id_list.append({
            'id': i[0],
            'title': i[1],
            'cover': f"https://{client.domain_list[0]}/media/albums/{i[0]}.jpg"
        })

    return photos_title_id_list


def get_favorites_photo(page: int) -> List[dict]:
    photos_title_id_list = []

    for i in client.favorite_folder(page):
        photos_title_id_list.append({
            'id': i[0],
            'title': i[1],
            'cover': f"https://{client.domain_list[0]}/media/albums/{i[0]}.jpg"
        })

    return photos_title_id_list


def decode_and_decode(JMclient: AbstractJmClient, img_url, scramble_id=None) -> BytesIO:
    if scramble_id is None:
        scramble_id = JmMagicConstants.SCRAMBLE_220980
    img_content = JMclient.get_jm_image(img_url).content
    num = JmImageTool.get_num_by_url(scramble_id, img_url)
    img_src = JmImageTool.open_image(img_content)
    if num == 0:
        return img_content

    import math
    w, h = img_src.size
    # 创建新的解密图片
    img_decode = Image.new("RGB", (w, h))
    remainder = h % num
    copyW = w
    for i in range(num):
        copyH = math.floor(h / num)
        py = copyH * i
        y = h - (copyH * (i + 1)) - remainder

        if i == 0:
            copyH += remainder
        else:
            py += remainder

        img_decode.paste(
            img_src.crop((0, y, copyW, y + copyH)),
            (0, py, copyW, py + copyH)
        )

    bytesIO = BytesIO()
    img_decode.save(bytesIO, format="WEBP")

    return bytesIO


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6987, debug=True)
