# 导入所需的标准库
from time import time
import requests
import json
import uuid
import hashlib

# 获取HTTP客户端（requests的session对象）
def get_http_client():
    return requests.session()

# 结果说明
# {
#     "OcrInfo": [
#         {
#             "Text": "...",图片中的全部文字
#             "Detail": [图片中的内容详情
#                 {
#                     "Type": "",内容类型，PrintedText｜WrittenText｜PrintedFormula ｜ WrittenFormula ｜ Illustration ｜ Stamp 等分别表示印刷文字｜手写文字｜印刷公式｜手写公式 ｜插图｜印章等
#                     "Value": "",	内容值
#                     "Confidence": 1,	内容置信度
#                     "InGraph": false,当图片内容为文本时，文本是否在图片中的插图、印章、流程图等其中
#                     "ColumnIndex": -1,当内容在表格中时，所在表格单元格的列索引
#                     "RowIndex": -1,	当内容在表格中时，所在表格单元格的行索引
#                     "ColumnSpan": -1,当内容在表格中时，所在表格单元格的列合并信息
#                     "RowSpan": -1当内容在表格中时，所在表格单元格的行合并信息
#                     "PageIndex":-1输入为pdf时，内容所在的pdf页面索引        
#                 }
#             ]
#         }
#     ]
# }


# 构造OCR请求参数
# client_id: 客户端ID
# client_secret: 客户端密钥
def create_demo_param(client_id, client_secret):
    business = "vision"  # 业务类型
    sign_method = "SHA3-256"  # 签名方法
    sign_nonce = uuid.uuid4().hex  # 随机字符串，防重放
    timestamp = int(time() * 1000)  # 当前时间戳（毫秒）
    signature = get_signature(client_id, client_secret, business, sign_method, sign_nonce, timestamp)  # 生成签名
    req_id = uuid.uuid4().hex  # 请求唯一ID

    # 构造请求参数字典
    param = {
        "dataUrl": "https://download-obs.cowcs.com/cowtransfer/cowtransfer/30466/f40caa628f80449594f908359d8c3675.pdf?auth_key=1752598135-4aa6ea237c5e452c9dc7a49bbb239a3b-0-999806cab939303390cf2e9dc67cabd0&biz_type=1&business_code=COW_TRANSFER&channel_code=COW_CN_WEB&response-content-disposition=attachment%3B%20filename%3D%25E3%2580%25902.%25E5%2590%2588%25E5%2590%258C%25E3%2580%2591%25E6%2588%25BF%25E5%25B1%258B%25E6%259F%25A5%25E9%25AA%258C%25E7%25AE%25A1%25E7%2590%2586%25E7%25B3%25BB%25E7%25BB%259F%25EF%25BC%2588%25E4%25B8%2580%25E6%259C%259F%25EF%25BC%2589%25E5%25BC%2580%25E5%258F%2591%25E6%259C%258D%25E5%258A%25A1%25E9%2587%2587%25E8%25B4%25AD%25E9%25A1%25B9%25E7%259B%25AE%25E5%2590%2588%25E5%2590%258C.pdf%3Bfilename*%3Dutf-8%27%27%25E3%2580%25902.%25E5%2590%2588%25E5%2590%258C%25E3%2580%2591%25E6%2588%25BF%25E5%25B1%258B%25E6%259F%25A5%25E9%25AA%258C%25E7%25AE%25A1%25E7%2590%2586%25E7%25B3%25BB%25E7%25BB%259F%25EF%25BC%2588%25E4%25B8%2580%25E6%259C%259F%25EF%25BC%2589%25E5%25BC%2580%25E5%258F%2591%25E6%259C%258D%25E5%258A%25A1%25E9%2587%2587%25E8%25B4%25AD%25E9%25A1%25B9%25E7%259B%25AE%25E5%2590%2588%25E5%2590%258C.pdf&user_id=1033100132874430466&x-verify=1",  # 图片URL
        "dataType": "pdf",  # 输入文件类型，image或者pdf
        "serviceOption": "ocr",  # 服务大类，ocr｜typeset｜structure｜scan
        "inputConfigs": "",  # 输入配置，用于配置输入数据内容，e.g."{\"function_option\":\"work_scene\"}"
        "outputConfigs": "",  # 输出配置，用于配置输出数据内容，e.g. '{"need_return_image":"True"}'
        "reqId": req_id,  # 请求ID, 用于问题定位
        "clientId": client_id,  # 客户端ID
        "signMethod": sign_method,  # 签名方法
        "signNonce": sign_nonce,  # 随机字符串
        "timestamp": timestamp,  # 时间戳字符串，参与加密计算，用户自己设置，不做格式要求
        "signature": signature  # 根据加密算法计算出来的签名字符串，用于鉴权
    }
    return param

# 生成签名字符串
# 根据不同的sign_method选择不同的哈希算法
def get_signature(client_id, client_secret, business, sign_method, sign_nonce, timestamp):
    # 拼接原始字符串
    raw_str = f"{client_id}_{business}_{sign_method}_{sign_nonce}_{timestamp}_{client_secret}"
    utf8_bytes = raw_str.encode("utf-8")
    # 根据sign_method选择不同的摘要算法
    if sign_method.lower() == "sha256":
        digest = hashlib.sha256(utf8_bytes).hexdigest()
    elif sign_method.lower() == "sha1":
        digest = hashlib.sha1(utf8_bytes).hexdigest()
    elif sign_method.lower() == "md5":
        digest = hashlib.md5(utf8_bytes).hexdigest()
    elif sign_method.lower() in ["sha3-256", "sha3_256"]:
        digest = hashlib.sha3_256(utf8_bytes).hexdigest()
    else:
        raise ValueError("Unsupported sign method")  # 不支持的签名方法
    # 将摘要转换为小写十六进制字符串
    sign = digest.lower()
    return sign

# 主程序入口
def main():
    client_id = 'test_AJ0715'  # 客户端ID（请替换为实际值）
    client_secret = 'GZAJ0715'  # 客户端密钥（请替换为实际值）
    http_client = get_http_client()  # 获取HTTP客户端
    param = create_demo_param(client_id, client_secret)  # 构造请求参数
    req_id = uuid.uuid4().hex  # 生成请求ID（未使用）
    url = "https://scan-business.quark.cn/vision"  # OCR服务接口地址
    headers = {
        "Content-Type": "application/json",
    }
    # 发送POST请求
    response = http_client.post(url, json=param, headers=headers)
    if response.status_code == 200:
        body = response.json()  # 解析响应体
        code = body.get("code")  # 获取返回码
        # 参照结果说明，存储获取到的内容
        ocr_info = body.get("data", {}).get("OcrInfo", [])
        # 这里将内容存储到本地文件，便于后续分析
        import json
        with open("ocr_result.json", "w", encoding="utf-8") as f:
            json.dump({"OcrInfo": ocr_info}, f, ensure_ascii=False, indent=4)
        print("已将OcrInfo内容存储到 ocr_result.json 文件中。")
        print("body.keys():", body.keys())
        print("ocr request result:", code)
    else:
        print("http request error")  # 请求失败

# 程序入口判断
if __name__ == "__main__":
    main()