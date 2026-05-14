import json
import time
import os
import cv2
import numpy as np
import pyautogui
import keyboard
import re

# =========================================================
# COMSOL 自动控制配置生成器（新版）
#
# 新逻辑：
#
# 1. 用户一路点击直到输入框获得光标
# 2. 程序只记录“到达输入状态”的流程
# 3. 最后按Q结束录制
# 4. 第二个文件直接：
#    Ctrl+A -> Backspace -> Ctrl+V
#
# 不再单独录制：
# - 点击输入框
#
# 稳定性大幅提高
# =========================================================

print("\n================================================")
print("COMSOL 自动控制配置生成器")
print("================================================\n")

# =========================================================
# 基础参数
# =========================================================

check_interval = input(
    "请输入检测间隔（秒）[默认60]: "
)

check_interval = (
    int(check_interval)
    if check_interval else 60
)

no_error_limit = input(
    "请输入连续无报错退出次数 [默认10]: "
)

no_error_limit = (
    int(no_error_limit)
    if no_error_limit else 10
)

# =========================================================
# 错误图标
# =========================================================

print("\n================================================")
print("错误图标设置")
print("================================================\n")

while True:

    error_icon_path = input(
        "请输入错误图标路径（例如 D:/error.JPG ）:\n"
    )

    if not os.path.exists(error_icon_path):

        print("\n错误：文件不存在\n")

        continue

    try:

        test_img = cv2.imdecode(
            np.fromfile(
                error_icon_path,
                dtype=np.uint8
            ),
            cv2.IMREAD_COLOR
        )

    except:

        test_img = None

    if test_img is None:

        print("\n错误：图片无法读取，请检查jpg/png格式\n")

        continue

    print("\n图标读取成功")

    height, width = test_img.shape[:2]

    print(f"图标尺寸：{width} x {height}")

    confirm = input(
        "\n确认使用该图标？(y/n): "
    )

    if confirm.lower() == 'y':

        break

# =========================================================
# 输入模板
# =========================================================

print("\n================================================")
print("输入模板设置")
print("================================================\n")

print("请直接输入 range() 括号内内容")
print("常量请直接写数字")
print("变量请写 n1、n2、n3 ...\n")

print("示例：")
print("0,n1,0.5")
print("n1,n2,0.5")
print("0,0.001,n1")
print("n1,n2,n3\n")

input_content = input(
    "请输入括号内内容: "
)

# =========================================================
# 自动识别变量
# =========================================================

variables_found = re.findall(
    r'n\d+',
    input_content
)

variables_found = list(
    dict.fromkeys(
        variables_found
    )
)

# =========================================================
# 配置变量
# =========================================================

variables = []

for var_name in variables_found:

    print("\n----------------------------------------")
    print(f"配置变量 {var_name}")
    print("----------------------------------------\n")

    start_value = float(
        input("最小值: ")
    )

    end_value = float(
        input("最大值: ")
    )

    increment = float(
        input("步长: ")
    )

    sequence = []

    current = start_value

    while current <= end_value:

        sequence.append(current)

        current += increment

    variables.append({

        "name": var_name,

        "start": start_value,

        "end": end_value,

        "increment": increment,

        "sequence": sequence
    })

# =========================================================
# OCR关键字
# =========================================================

print("\n================================================")
print("OCR关键字设置")
print("================================================\n")

step_keyword = input(
    "请输入步长输入框OCR关键字 [默认: range]: "
)

step_keyword = (
    step_keyword
    if step_keyword else "range"
)

# =========================================================
# 录制函数
# =========================================================

def record_steps(stage_name):

    print("\n================================================")
    print(f"开始录制：{stage_name}")
    print("================================================")
    print("操作说明：")
    print("1. 鼠标移动到目标位置")
    print("2. 按 SPACE 记录")
    print("3. 输入重复次数")
    print("4. repeat=-1 表示无限点击")
    print("5. 最后让输入框获得光标")
    print("6. 按 Q 结束录制")
    print("================================================\n")

    steps = []

    while True:

        # =================================================
        # Q结束
        # =================================================

        if keyboard.is_pressed('q'):

            print(f"\n{stage_name} 录制结束\n")

            while keyboard.is_pressed('q'):

                time.sleep(0.05)

            time.sleep(0.3)

            break

        # =================================================
        # SPACE记录
        # =================================================

        if keyboard.is_pressed('space'):

            x, y = pyautogui.position()

            print(f"\n记录坐标: ({x}, {y})")

            repeat = input(
                "请输入重复次数（1=普通点击，-1=无限点击）: "
            )

            try:

                repeat = int(repeat)

            except:

                repeat = 1

            interval = input(
                "请输入点击间隔秒数 [默认0.5]: "
            )

            try:

                interval = float(interval)

            except:

                interval = 0.5

            steps.append({

                "x": x,

                "y": y,

                "repeat": repeat,

                "interval": interval
            })

            print("步骤已保存")

            # 防止SPACE长按重复触发
            while keyboard.is_pressed('space'):

                time.sleep(0.05)

            time.sleep(0.3)

    return steps

# =========================================================
# 录制流程
# =========================================================

print("\n================================================")
print("录制流程说明")
print("================================================")
print("你需要：")
print("从错误弹窗开始")
print("一路点击")
print("直到输入框获得输入光标")
print("然后按Q结束")
print("================================================\n")

workflow_steps = record_steps(
    "到达输入框流程"
)

# =========================================================
# 关闭设置页面
# =========================================================

close_setting_steps = record_steps(
    "关闭设置页面"
)

# =========================================================
# 重新开始计算
# =========================================================

start_solver_steps = record_steps(
    "重新开始计算"
)

# =========================================================
# 配置生成
# =========================================================

config = {

    "CHECK_INTERVAL": check_interval,

    "NO_ERROR_LIMIT": no_error_limit,

    "STEP_KEYWORD": step_keyword,

    "ERROR_ICON_PATH": error_icon_path,

    "VARIABLES": variables,

    "INPUT_TEMPLATE": input_content,

    # 新版统一流程
    "WORKFLOW_STEPS": workflow_steps,

    "CLOSE_SETTING_STEPS": close_setting_steps,

    "START_SOLVER_STEPS": start_solver_steps
}

# =========================================================
# 保存配置
# =========================================================

with open(
    "config.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        config,
        f,
        indent=4,
        ensure_ascii=False
    )

# =========================================================
# 完成
# =========================================================

print("\n================================================")
print("配置生成完成")
print("已生成 config.json")
print("================================================\n")

print(json.dumps(
    config,
    indent=4,
    ensure_ascii=False
))