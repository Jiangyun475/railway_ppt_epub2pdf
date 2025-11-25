import os
from Test_converter import convert_epub_to_pdf

# 你的 EPUB 文件路径
# epub_file = r"D:\Users\jiangyun\Downloads\置身事内：中国政府与经济发展 (兰小欢) (Z-Library).epub"
epub_file = r"D:\Users\jiangyun\Downloads\以利为利：财政关系与地方政府行为 (周飞舟) (Z-Library).epub"


# 你想保存 PDF 的位置（比如桌面）
output_pdf = r"C:\Users\jiangyun\Desktop\output_test.pdf"

print("开始转换...")
convert_epub_to_pdf(epub_file, output_pdf)
print(f"转换结束，请检查: {output_pdf}")