import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
from matplotlib import font_manager as fm
import numpy as np


def draw_afpn_diagram():
    plt.figure(figsize=(12, 8))
    ax = plt.gca()

    # 设置图层参数
    layer_params = {
        'C3': {'pos': (1, 4), 'label': 'Backbone\nC3 (Shallow)', 'color': '#FFD700'},
        'C4': {'pos': (1, 2), 'label': 'Backbone\nC4 (Middle)', 'color': '#FFA500'},
        'C5': {'pos': (1, 0), 'label': 'Backbone\nC5 (Deep)', 'color': '#FF8C00'},
        'AFPN': {'pos': (3, 2), 'label': 'AFPN\nFusion Module', 'color': '#1E90FF'},
        'P3': {'pos': (5, 4), 'label': 'Output\nP3 (High-res)', 'color': '#32CD32'},
        'P4': {'pos': (5, 2), 'label': 'Output\nP4 (Mid-res)', 'color': '#228B22'},
        'P5': {'pos': (5, 0), 'label': 'Output\nP5 (Low-res)', 'color': '#006400'},
        'FeatureFusion': {'pos': (3, 3.3), 'label': 'Feature\nFusion', 'color': '#87CEFA'},
        'CrossScale': {'pos': (3, 0.7), 'label': 'Cross-scale\nConnection', 'color': '#87CEFA'}
    }

    # 绘制层节点
    for name, params in layer_params.items():
        ax.add_patch(patches.Rectangle(
            (params['pos'][0] - 0.5, params['pos'][1] - 0.5), 1, 1,
            facecolor=params['color'], alpha=0.8, edgecolor='black',
            linewidth=1.5
        ))
        plt.text(
            params['pos'][0], params['pos'][1],
            params['label'],
            ha='center', va='center', fontsize=10, fontweight='bold'
        )

    # 绘制连接线
    connections = [
        # 标准连接
        ('C3', 'FeatureFusion', 'black', 1.5, '-'),
        ('C4', 'AFPN', 'black', 1.5, '-'),
        ('C5', 'CrossScale', 'black', 1.5, '-'),
        ('FeatureFusion', 'P3', 'green', 1.5, '-'),
        ('AFPN', 'P4', 'green', 1.5, '-'),
        ('CrossScale', 'P5', 'green', 1.5, '-'),

        # AFPN核心创新: 非相邻层直接连接
        ('C3', 'P5', 'purple', 2.5, '--'),
        ('C5', 'P3', 'purple', 2.5, '--'),

        # AFPN内部连接
        ('FeatureFusion', 'AFPN', 'gray', 1.0, '-'),
        ('CrossScale', 'AFPN', 'gray', 1.0, '-')
    ]

    # 绘制所有连接线
    for src, dst, color, width, linestyle in connections:
        src_pos = layer_params[src]['pos']
        dst_pos = layer_params[dst]['pos']

        # 添加箭头
        plt.annotate("",
                     xy=dst_pos, xycoords='data',
                     xytext=src_pos, textcoords='data',
                     arrowprops=dict(
                         arrowstyle="->",
                         color=color,
                         linewidth=width,
                         linestyle=linestyle,
                         alpha=0.8,
                         shrinkA=15,  # 箭头起点偏移
                         shrinkB=15  # 箭头终点偏移
                     )
                     )

    # 添加图例 (右上角)
    legend_elements = [
        Line2D([0], [0], color='purple', lw=2, linestyle='--', label='Cross-layer Connection'),
        Line2D([0], [0], color='black', lw=2, label='Standard Connection'),
        Line2D([0], [0], color='green', lw=2, label='Output Path'),
        patches.Patch(facecolor='#1E90FF', alpha=0.8, label='AFPN Module'),
        patches.Patch(facecolor='#87CEFA', alpha=0.8, label='Fusion Components')
    ]
    plt.legend(handles=legend_elements, loc='upper right', fontsize=10,
               bbox_to_anchor=(1.0, 1.0), framealpha=0.9)

    # 添加标题和说明 (顶部中央)
    plt.title('AFPN Architecture for Crop Disease Detection',
              fontsize=16, pad=20, fontweight='bold')

    # 特征说明 (左侧)
    plt.text(-0.8, 4, "Shallow Features:\n- High resolution\n- Detail retention",
             ha='left', fontsize=10, color='#555555', bbox=dict(facecolor='#f8f8f8', alpha=0.7))
    plt.text(-0.8, 0, "Deep Features:\n- Rich semantics\n- Large receptive field",
             ha='left', fontsize=10, color='#555555', bbox=dict(facecolor='#f8f8f8', alpha=0.7))

    # 输出说明 (右侧)
    plt.text(6.2, 4, "P3 Output:\n- Small lesions\n- Early detection",
             ha='right', fontsize=10, color='#555555', bbox=dict(facecolor='#f8f8f8', alpha=0.7))
    plt.text(6.2, 0, "P5 Output:\n- Large areas\n- Severe symptoms",
             ha='right', fontsize=10, color='#555555', bbox=dict(facecolor='#f8f8f8', alpha=0.7))

    # 关键创新标注 (底部中央)
    plt.text(3, -1.8,
             "Key Innovation: Direct cross-layer connections enable\n"
             "simultaneous utilization of shallow details (C3) and deep semantics (C5)\n"
             "→ Improves mAP by 3.31% for small lesion detection",
             ha='center', fontsize=11, bbox=dict(facecolor='#f0f8ff', alpha=0.7))

    # 连接标注
    plt.text(2, 3.5, "Feature Extraction", ha='center', fontsize=9, color='black')
    plt.text(4, 3.5, "Feature Fusion", ha='center', fontsize=9, color='green')
    plt.text(3, 4.5, "Cross-layer Flow", ha='center', fontsize=9, color='purple',
             bbox=dict(facecolor='#f9f2ff', alpha=0.7))

    plt.xlim(-1.5, 7.5)
    plt.ylim(-2.5, 6)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig('afpn_architecture_optimized.png', dpi=300, bbox_inches='tight')
    plt.show()


# 生成示意图
draw_afpn_diagram()