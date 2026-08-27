import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors as mcolors


def create_compression_table():
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.axis('off')

    # 表格标题
    plt.title("Suppl. Table 2: Model Compression Results (YOLOv8-n)",
              fontsize=14, pad=20, weight='bold', loc='left')

    # 列标题
    columns = ["Model", "Precision", "Model Size (MB)", "mAP@0.5", "Latency (ms)*", "Memory (GB)"]
    col_colors = ["#D3D3D3", "#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#79706E"]

    # 数据内容
    data = [
        ["FP32 (Baseline)", "76.5", "14.2", "68.4", "5.3", "1.8"],
        ["FP16", "76.1 (-0.4)", "7.1 (-50%)", "67.9 (-0.5)", "3.1 (-41%)", "1.2 (-33%)"],
        ["INT8 (PTQ)", "74.3 (-2.2)", "3.6 (-75%)", "65.1 (-3.3)", "2.2 (-58%)", "0.9 (-50%)"],
        ["INT8 (QAT)", "75.8 (-0.7)", "3.6 (-75%)", "66.7 (-1.7)", "2.1 (-60%)", "0.9 (-50%)"]
    ]

    # 绘制表格
    table = plt.table(cellText=data,
                     colLabels=columns,
                     colColours=[mcolors.to_rgba(c, 0.3) for c in col_colors],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0, 1, 0.8])

    # 格式化表格
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1, 1.5)

    # 高亮关键数据
    for (i, j), cell in table.get_celld().items():
        if i == 0:  # 标题行
            cell.set_text_props(weight='bold')
        if "(-" in cell.get_text().get_text():  # 负值标红
            cell.set_text_props(color='red')
        if j == 4 and i > 0:  # Latency列 (现在第5列)
            cell.set_facecolor("#FFF2CC")

    # 添加脚注
    plt.figtext(0.5, 0.05,
                "* Latency measured on NVIDIA Jetson AGX Xavier with TensorRT 8.4",
                ha='center', fontsize=10, style='italic')

    plt.tight_layout()
    plt.savefig("suppl_table2_compression.png", dpi=600, bbox_inches='tight')
    plt.show()


create_compression_table()