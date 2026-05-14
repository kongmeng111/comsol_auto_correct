import json
import time
import cv2
import numpy as np
import pyautogui
import keyboard
import pyperclip
import itertools

from paddleocr import PaddleOCR
from PIL import ImageGrab

# =========================================================
# COMSOL 自动控制器
#
# 功能：
# 1. 读取 config.json
# 2. OCR识别中文/英文/数字
# 3. 模板匹配错误图标
# 4. 自动点击COMSOL
# 5. 自动修改 range(...)
# 6. 自动重新运行
# 7. 每次启动自动初始化
#
# 使用要求：
# 1. COMSOL必须全屏
# 2. COMSOL必须在最前面
# 3. 不允许改变布局
# =========================================================

# =========================================================
# 安全机制
# 鼠标移动到左上角可强制终止
# =========================================================

pyautogui.FAILSAFE = True

# =========================================================
# 启动提示
# =========================================================

print("\n================================================")
print("COMSOL 自动控制器启动")
print("支持中文 / 英文 / 数字 OCR")
print("每次运行自动初始化")
print("鼠标移动到左上角可强制停止")
print("按Q随时退出")
print("================================================\n")

print("5秒后开始运行...")
time.sleep(5)

# =========================================================
# 读取配置
# =========================================================

with open("config.json", "r", encoding="utf-8") as f:

    config = json.load(f)

CHECK_INTERVAL = config["CHECK_INTERVAL"]

NO_ERROR_LIMIT = config["NO_ERROR_LIMIT"]

STEP_KEYWORD = config["STEP_KEYWORD"]

ERROR_ICON_PATH = config["ERROR_ICON_PATH"]

VARIABLES = config["VARIABLES"]

INPUT_TEMPLATE = config["INPUT_TEMPLATE"]

OPEN_SETTING_STEPS = config["OPEN_SETTING_STEPS"]

INPUT_BOX_STEPS = config["INPUT_BOX_STEPS"]

CLOSE_SETTING_STEPS = config["CLOSE_SETTING_STEPS"]

START_SOLVER_STEPS = config["START_SOLVER_STEPS"]

# =========================================================
# OCR初始化
# =========================================================

ocr = PaddleOCR(
    use_angle_cls=True,
    lang='ch'
)

# =========================================================
# 初始化变量组合
# =========================================================

print("初始化变量组合...\n")

variable_names = []

variable_sequences = []

for var in VARIABLES:

    variable_names.append(var["name"])

    variable_sequences.append(var["sequence"])

all_combinations = list(
    itertools.product(*variable_sequences)
)

current_combination_index = 0

print(f"变量组合总数: {len(all_combinations)}\n")

# =========================================================
# 截图
# =========================================================

def capture_screen():

    img = ImageGrab.grab()

    img = np.array(img)

    img = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2BGR
    )

    return img

# =========================================================
# OCR识别
# =========================================================

def run_ocr(img):

    result = ocr.ocr(
        img,
        cls=True
    )

    texts = []

    for line in result:

        if line is None:
            continue

        for item in line:

            box = item[0]

            text = item[1][0]

            score = item[1][1]

            x_coords = [p[0] for p in box]
            y_coords = [p[1] for p in box]

            x1 = int(min(x_coords))
            y1 = int(min(y_coords))
            x2 = int(max(x_coords))
            y2 = int(max(y_coords))

            texts.append({

                "text": text,

                "box": (
                    x1,
                    y1,
                    x2,
                    y2
                ),

                "score": score
            })

    return texts

# =========================================================
# 查找OCR关键字
# =========================================================

def find_keyword(texts, keyword):

    for item in texts:

        text = item["text"]

        if keyword.lower() in text.lower():

            return item

    return None

# =========================================================
# 检测错误图标
# 支持中文路径
# =========================================================

def detect_error_icon():

    screen = capture_screen()

    try:

        template = cv2.imdecode(
            np.fromfile(
                ERROR_ICON_PATH,
                dtype=np.uint8
            ),
            cv2.IMREAD_COLOR
        )

    except:

        template = None

    if template is None:

        print("\n无法读取错误图标")

        return False

    result = cv2.matchTemplate(
        screen,
        template,
        cv2.TM_CCOEFF_NORMED
    )

    threshold = 0.8

    locations = np.where(
        result >= threshold
    )

    if len(locations[0]) > 0:

        return True

    return False

# =========================================================
# 点击
# =========================================================

def click(x, y):

    pyautogui.moveTo(
        x,
        y,
        duration=0.2
    )

    pyautogui.click()

# =========================================================
# 执行录制步骤
# =========================================================

def execute_steps(steps):

    for step in steps:

        x = step["x"]

        y = step["y"]

        repeat = step["repeat"]

        interval = step["interval"]

        # 无限点击
        if repeat == -1:

            print("\n开始无限点击")
            print("按Q结束当前无限点击")

            while True:

                if keyboard.is_pressed('q'):

                    print("\n无限点击结束")

                    time.sleep(0.5)

                    break

                click(x, y)

                time.sleep(interval)

        # 普通点击
        else:

            for i in range(repeat):

                click(x, y)

                time.sleep(interval)

# =========================================================
# 生成输入字符串
# =========================================================

def generate_input_string():

    global current_combination_index

    if current_combination_index >= len(all_combinations):

        return None

    values = all_combinations[
        current_combination_index
    ]

    current_combination_index += 1

    # 自动补 range(...)
    result = f"range({INPUT_TEMPLATE})"

    for i in range(len(variable_names)):

        name = variable_names[i]

        value = values[i]

        result = result.replace(
            name,
            str(value)
        )

    return result

# =========================================================
# 修改输入框
# =========================================================

def modify_input():

    input_text = generate_input_string()

    if input_text is None:

        print("\n所有变量组合已测试完成")

        return False

    print("\n================================================")
    print("新的输入内容")
    print("================================================\n")

    print(input_text)

    # =====================================================
    # 点击输入框
    # =====================================================

    print("\n执行输入框点击流程")

    execute_steps(
        INPUT_BOX_STEPS
    )

    time.sleep(0.5)

    # =====================================================
    # OCR确认输入框
    # =====================================================

    print("\nOCR识别当前界面...")

    screen = capture_screen()

    texts = run_ocr(screen)

    keyword_result = find_keyword(
        texts,
        STEP_KEYWORD
    )

    if keyword_result:

        print("\n已识别到目标关键字")

    else:

        print("\n警告：未识别到关键字")
        print("仍继续执行")

    # =====================================================
    # 清空输入框
    # =====================================================

    print("\n清空输入框")

    for i in range(20):

        pyautogui.press(
            'backspace'
        )

    for i in range(20):

        pyautogui.press(
            'delete'
        )

    time.sleep(0.3)

    # =====================================================
    # 输入新内容
    # =====================================================

    print("\n输入新内容")

    pyperclip.copy(
        input_text
    )

    pyautogui.hotkey(
        'ctrl',
        'v'
    )

    time.sleep(0.3)

    pyautogui.press(
        'enter'
    )

    print("\n输入完成")

    return True

# =========================================================
# 主程序
# =========================================================

def main():

    no_error_count = 0

    while True:

        # 手动退出
        if keyboard.is_pressed('q'):

            print("\n检测到Q键")

            print("程序终止")

            break

        print("\n================================================")
        print("开始检测错误图标...")
        print("================================================")

        # =================================================
        # 检测错误
        # =================================================

        found_error = detect_error_icon()

        # =================================================
        # 无错误
        # =================================================

        if not found_error:

            no_error_count += 1

            print("\n未检测到错误")

            print(
                f"连续正常次数: {no_error_count}"
            )

            if no_error_count >= NO_ERROR_LIMIT:

                print("\n================================================")
                print("仿真稳定")
                print("程序自动结束")
                print("================================================\n")

                break

        # =================================================
        # 检测到错误
        # =================================================

        else:

            no_error_count = 0

            print("\n================================================")
            print("检测到错误图标")
            print("================================================")

            # =============================================
            # 进入设置页
            # =============================================

            print("\n执行进入设置流程")

            execute_steps(
                OPEN_SETTING_STEPS
            )

            time.sleep(1)

            # =============================================
            # 修改输入
            # =============================================

            success = modify_input()

            if not success:

                print("\n修改失败")

                break

            time.sleep(1)

            # =============================================
            # 关闭设置页
            # =============================================

            print("\n执行关闭设置流程")

            execute_steps(
                CLOSE_SETTING_STEPS
            )

            time.sleep(1)

            # =============================================
            # 重新开始计算
            # =============================================

            print("\n执行重新计算流程")

            execute_steps(
                START_SOLVER_STEPS
            )

            print("\n已重新开始计算")

        print(f"\n等待 {CHECK_INTERVAL} 秒...\n")

        time.sleep(
            CHECK_INTERVAL
        )

# =========================================================
# 启动
# =========================================================

if __name__ == "__main__":

    main()