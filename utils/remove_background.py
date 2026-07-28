from PIL import Image

def remove_background(img_bytes: bytes, remover) -> Image.Image:
    img = img_bytes.convert('RGB')
    out = remover.process(img, type='rgba')
    bg = Image.new('RGBA', out.size, (255, 255, 255, 255))
    bg.paste(out, mask=out.split()[3])
    return bg.convert('RGB')