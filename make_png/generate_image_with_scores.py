import ast
from PIL import Image, ImageDraw, ImageFont

geisha_colors = [
    "#8A2BE2", "#FF0000", "#FFFF00", "#FFA500",
    "#0000FF", "#008000", "#FFC0CB"
]

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# Read vectors and scores
vectors = []
with open("input.txt", "r") as f:
    for line in f:
        if ":" in line:
            vec_str, val_str = line.strip().split(":")
            vector = ast.literal_eval(vec_str.strip())
            value = float(val_str.strip())
            vectors.append((vector, value))

square_size = 30
padding = 10
font_size = 16

try:
    font = ImageFont.truetype("arial.ttf", font_size)
except:
    font = ImageFont.load_default()

rows = len(vectors)
cols = max(sum(v) for v, _ in vectors)
img_width = cols * square_size + 100  # extra for text
img_height = rows * (square_size + padding)

print(f"Generating image {img_width}x{img_height} px")

img = Image.new("RGB", (img_width, img_height), "white")
draw = ImageDraw.Draw(img)

for row_index, (vector, value) in enumerate(vectors):
    y = row_index * (square_size + padding)
    x = 0
    for color_index, count in enumerate(vector):
        color = hex_to_rgb(geisha_colors[color_index])
        for _ in range(count):
            draw.rectangle(
                [x, y, x + square_size - 1, y + square_size - 1],
                fill=color,
                outline="black"
            )
            x += square_size
    draw.text((x + 10, y + square_size // 4), f"{value:.6f}", fill="black", font=font)

img.save("hanamikoji_all_vectors.png")
print("Saved final image as hanamikoji_all_vectors.png")
