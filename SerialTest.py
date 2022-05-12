import re
import serial.tools.list_ports
import traceback
import time
from _datetime import datetime
import sys

port_list = list(serial.tools.list_ports.comports())  # 获取当前可用串口列表123123123123
now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
filename = ".\\Logs\\" + now + ".txt"
Logfile = open(filename, 'w', encoding="gbk")


# 向日志文件写入时间戳
def LogWriteNow(string):
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S ")
    Logfile.write(now)
    Logfile.write(str(string))


# 判断元素是否在列表中 --> (需要判断的元素, 需要判断的列表)
def IsInList(string, inputlist):
    flag = False
    for i in inputlist:
        if string in str(i).replace(" ", ""):
            flag = True
            break
        else:
            flag = False
    return flag


# 判断板卡型号及位置 --> (预设的list, 输入的list)
def GetCardType(SavedList, InputList):
    for i in SavedList:
        flag = 0
        for j in i:
            if IsInList(j, InputList):
                flag += 1
            else:
                continue
        if flag == len(i):
            return SavedList.index(i)  # 判断flag长度是否为SavedList当中某一个元素列表的长度，如果是则返回这个列表的下标
    return -1  # 板卡未正常获取


# 判断板卡是否启动(是否处于INSERVICE状态) --> (从串口获取到的list, 预存的板卡型号list)
def IsCardRdy(InPutList, CardType):
    CurrentCardType = CardList[CardType]
    flag = 0
    for i in CurrentCardType:
        for j in InPutList:
            if str(i) in str(j).replace(" ", "") and "INSERVICE" in str(j):
                flag += 1
                break
            else:
                continue
    if flag == len(CurrentCardType):
        return True
    else:
        return False


# 循环输出列表中元素
def LoopPrintList(InputList):
    for i in InputList:
        print(str(i))


if __name__ == '__main__':
    # 选择串口
    print("当前可用串口:")
    LogWriteNow("Serial can be used:\n")
    if len(port_list) == 0:
        print("无可用串口")
        # Log
        LogWriteNow("There is no Serial can be used.\n")
    else:
        for i in range(0, len(port_list)):
            print(port_list[i], " .......... ", i + 1)
            # Log
            LogInput = str(port_list[i]) + " .......... " + str(i + 1) + "\n"
            LogWriteNow(LogInput)
    print("请选择串口:")
    SelectSerial = input()
    # 选择串口

    # 打开串口
    while len(SelectSerial) == 0:
        SelectSerial = input()
    try:
        portx = str(port_list[int(SelectSerial) - 1])
        bps = 9600
        timex = 0.5
        ser = serial.Serial(portx[0:5], bps, timeout=timex)
        # Log
        LogInput = "Option " + SelectSerial + " has been chosen\n"
        LogWriteNow(LogInput)
        LogWriteNow("Serial detailed parameters:\n")
        LogInput = str(ser) + "\n"
        LogWriteNow(LogInput)
        # 串口通信

        # 串口登录
        inputdata = "\n"
        ser.write(inputdata.encode("gbk"))
        SerRead = ser.readlines(ser.in_waiting)
        count = 0
        while not IsInList("ZXAN(config)#", SerRead):
            if IsInList("RETURN", SerRead):
                ser.write("\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogInput = "<--" + str(SerRead) + "\n"
                LogWriteNow(LogInput)
                LogWriteNow(r"-->\n")
                Logfile.write("\n")
            elif IsInList("ZXAN>", SerRead):
                ser.write("enable\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogWriteNow("<--ZXAN>\n")
                LogWriteNow("-->enable\n")
            elif IsInList("Password:", SerRead):
                ser.write("zxr10\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogWriteNow("<--Password:\n")
                LogWriteNow("-->zxr10\n")
            elif IsInList("ZXAN#", SerRead):
                ser.write("config terminal\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogWriteNow("<--ZXAN#\n")
                LogWriteNow("-->config terminal\n")
            elif IsInList("=>", SerRead):
                ser.write("boot\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogWriteNow("<--=>\n")
                LogWriteNow("-->boot\n")
            else:
                ser.write("\n".encode("gbk"))
                SerRead = ser.readlines(ser.in_waiting)
                # Log
                LogWriteNow(r"-->\n")
                Logfile.write("\n")
                # Log
                if count == 0:
                    print('设备正在启动，请稍候')
                    count = 1
                elif 0 < count < 4:
                    print('.', end="")
                    count = count + 1
                elif count == 4:
                    print('\r', end="")
                    count = 1
            time.sleep(1)
        print("\r设备登录成功!")
        # Log
        LogWriteNow("Login succeed!\n")
        # 串口登录

        # 查询板卡型号、状态
        PonArr = ['32', '24', '16', '16', '8']  # PON口数量，对应CardList列表
        PonList = ["16", "16"], \
                  ["16", "8"], \
                  ["16"], \
                  ["8", "8"], \
                  ["8"]  # PON口数量列表，对应CardList列表中的不同型号板卡
        CardList = ["1ETGH", "2ETGH", "3PRAM", "4SMXA"], \
                   ["1ETGH", "2ETGO", "3PRAM", "4SMXA"], \
                   ["1ETGH", "3PRAM", "4SMXA"], \
                   ["1ETGO", "2ETGO", "3PRAM", "4SMXA"], \
                   ["1ETGO", "3PRAM", "4SMXA"]  # 初始化板卡型号列表
        count = 0
        TryTimes = 0
        while True:
            ser.write("show card\n".encode("gbk"))
            SerRead = ser.readlines(ser.in_waiting)
            # Log
            LogWriteNow("-->show card\n")
            LogWriteNow("<--\n")
            for i in SerRead:
                Logfile.write(str(i))
                Logfile.write("\n")
            # Log
            CardType = GetCardType(CardList, SerRead)
            if CardType >= 0:
                print("\r板卡型号获取成功，当前设备PON口数量为:", PonArr[CardType])  # 板卡型号获取成功，开始获取板卡状态
                # Log
                LogInput = "CardType is: " + str(CardList[CardType]) + "\n"
                LogWriteNow(LogInput)
                # Log
                count = 0
                while True:
                    ser.write("show card\n".encode("gbk"))
                    SerRead = ser.readlines(ser.in_waiting)
                    # Log
                    LogWriteNow("-->show card\n")
                    LogWriteNow("<--\n")
                    for i in SerRead:
                        Logfile.write(str(i))
                        Logfile.write("\n")
                    # Log
                    IsCardRdy(SerRead, CardType)
                    if IsCardRdy(SerRead, CardType):  # 板卡进入INSERVICE状态，开始进行配置
                        print("\r板卡启动成功!正在进行配置...")
                        # Log
                        LogWriteNow("Card is now in INSERVICE state!\n")
                        # Log
                        for i in range(0, len(PonList[CardType])):  # 开启PON口
                            for j in range(1, int(PonList[CardType][i]) + 1):
                                inputdata = "interface epon-olt_1/" + str(i + 1) + "/" + str(j) + "\n"
                                ser.write(inputdata.encode("gbk"))
                                ser.write("no shutdown\n".encode("gbk"))
                                ser.write("exit\n".encode("gbk"))
                                # Log
                                LogWriteNow("-->")
                                Logfile.write(inputdata)
                                LogWriteNow("-->no shutdown\n")
                                LogWriteNow("-->exit\n")
                                time.sleep(0.1)
                        # 配置管理VLAN
                        print("请输入管理VLAN:")
                        VLAN = 0
                        while not VLAN:
                            try:
                                VLAN = int(input())
                                if not 1 <= VLAN <= 4096:
                                    print("错误，请输入正确VLAN号:")
                                    # Log
                                    LogInput = str(VLAN) + " is input,it's an illegal VLAN. VLAN has been reset as '0'.\n"
                                    LogWriteNow(LogInput)
                                    VLAN = 0
                            except IndexError as e:
                                print("错误，请输入正确VLAN号:")
                                # Log
                                LogWriteNow("Wrong Value has been input. VLAN has been reset as '0'.\n")
                                VLAN = 0
                            except ValueError as e:
                                print("错误，请输入正确VLAN号:")
                                # Log
                                LogWriteNow("Wrong Value has been input. VLAN has been reset as '0'.\n")
                                VLAN = 0
                        inputdata = "vlan " + str(VLAN) + "\n" + "description MNG\nexit\n"
                        ser.write(inputdata.encode("gbk"))
                        # Log
                        LogInput = "Manage VLAN is: " + str(VLAN) + "\n"
                        LogWriteNow(LogInput)
                        LogInput = "-->vlan " + str(VLAN) + "\n"
                        LogWriteNow(LogInput)
                        LogWriteNow("-->description MNG\n")
                        LogWriteNow("-->exit\n")
                        # 配置管理IP
                        IP, Mask = '', ''
                        # 正则表达式匹配IP地址、掩码
                        PatternIP = re.compile(
                            r'((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}')
                        PatternMask = re.compile(
                            r'^(?:\d{1,2}|1\d\d|2[0-4]\d|25[0-5])(?:\.(?:\d{1,2}|1\d\d|2[0-4]\d|25[0-5])){3}$')
                        print("请输入管理IP:")
                        while not IP:
                            IP = input()
                            try:
                                m = PatternIP.search(IP)
                                if m is None:
                                    print("请输入正确格式的IP地址:")
                                    # Log
                                    LogInput = str(IP) + " is input,it's an illegal IP. IP has been reset as None.\n"
                                    LogWriteNow(LogInput)
                                    IP = ''
                                else:
                                    if len(IP) != len(m.group(0)):  # 判断输入的字符串和正则匹配到的是否一致，确保精准匹配
                                        print("请输入正确格式的IP地址:")
                                        # Log
                                        LogInput = str(IP) + " is input,it's an illegal IP. IP has been reset as None.\n"
                                        LogWriteNow(LogInput)
                                        IP = ''
                                    else:
                                        IP = m.group(0)
                            except Exception as e:
                                print(e)
                        print("请输入管理IP的掩码:")
                        while not Mask:
                            Mask = input()
                            try:
                                m = PatternMask.search(Mask)
                                if m is None:
                                    print("请输入正确格式的掩码:")
                                    # Log
                                    LogInput = str(Mask) + " is input,it's an illegal Mask. Mask has been reset as None.\n"
                                    LogWriteNow(LogInput)
                                    Mask = ''
                                else:
                                    if len(Mask) != len(m.group(0)):  # 判断输入的字符串和正则匹配到的是否一致，确保精准匹配
                                        print("请输入正确格式的掩码:")
                                        # Log
                                        LogInput = str(Mask) + " is input,it's an illegal Mask. Mask has been reset as None.\n"
                                        LogWriteNow(LogInput)
                                        Mask = ''
                                    else:
                                        Mask = m.group(0)
                            except Exception as e:
                                print(e)
                        inputdata = "interface vlan " + str(VLAN) + "\n"
                        ser.write(inputdata.encode("gbk"))
                        inputdata = "ip add " + IP + " " + Mask + "\n"
                        ser.write(inputdata.encode("gbk"))
                        ser.write("exit\n".encode("gbk"))
                        # Log
                        LogInput = "-->interface vlan " + str(VLAN) + "\n"
                        LogWriteNow(LogInput)
                        LogInput = "-->ip add " + IP + " " + Mask + "\n"
                        LogWriteNow(LogInput)
                        LogWriteNow("-->exit\n")

                        # 配置用户名密码
                        ser.write("service password-encryption\n".encode("gbk"))
                        ser.write("username wasu password wasu@123 privilege 15\n".encode("gbk"))
                        ser.write("username wasu password wasu@123 max-sessions 16\n".encode("gbk"))
                        ser.write("no ssh server only\n".encode("gbk"))
                        # Log
                        LogWriteNow("-->service password-encryption\n")
                        LogWriteNow("-->username wasu password wasu@123 privilege 15\n")
                        LogWriteNow("-->username wasu password wasu@123 max-sessions 16\n")
                        LogWriteNow("-->no ssh server only\n")

                        # 配置静态路由(此处默认管理IP为24位，如有变动需修改)
                        IPA, IPB, IPC = '', '', ''
                        IndexA, IndexB, IndexC = 0, 0, 0
                        IndexA = IP.find('.')
                        IndexB = IP.find('.', IndexA + 1)
                        IndexC = IP.find('.', IndexB + 1)
                        IPA = IP[0: IndexA]
                        IPB = IP[IndexA + 1:IndexB]
                        IPC = IP[IndexB + 1:IndexC]
                        inputdata = "ip route 0.0.0.0 0.0.0.0 " + IPA + '.' + IPB + '.' + IPC + '.' + '254\n'
                        ser.write(inputdata.encode("gbk"))
                        # Log
                        LogWriteNow("-->")
                        Logfile.write(inputdata)

                        # 配置上联口
                        ser.write("interface gei_1/4/1\n".encode("gbk"))
                        ser.write("no shutdown\n".encode("gbk"))
                        ser.write("switchport mode trunk\n".encode("gbk"))
                        inputdata = "switchport vlan " + str(VLAN) + " tag\n"
                        ser.write(inputdata.encode("gbk"))
                        ser.write("exit\nexit\nwrite".encode("gbk"))
                        # Log
                        LogWriteNow("-->interface gei_1/4/1\n")
                        LogWriteNow("-->no shutdown\n")
                        LogWriteNow("-->switchport mode trunk\n")
                        LogWriteNow("-->")
                        Logfile.write(inputdata)
                        LogWriteNow("-->exit\n")
                        LogWriteNow("-->exit\n")
                        LogWriteNow("-->write\n")
                        print("配置完成!")

                        Logfile.close()
                        sys.exit(0)
                    else:
                        if count == 0:
                            print('正在等待板卡启动，请稍候')
                            count = 1
                        elif 0 < count < 4:
                            print('.', end="")
                            count = count + 1
                        elif count == 4:
                            print('\r', end="")
                            count = 1
                        time.sleep(1)
                        continue
            elif TryTimes >= 99:  # 重复99次未获取到板卡型号时，询问是否继续等待
                print("\r长时间未获取到板卡型号，是否继续等待?")
                print("1.继续等待；2.退出等待")
                InputNum = 0
                while not InputNum:
                    try:
                        InputNum = int(input())
                        if not 1 <= InputNum <= 2:
                            print("错误，请输入正确的选项:")
                            InputNum = 0
                    except IndexError as e:
                        print("错误，请输入正确的选项:")
                        InputNum = 0
                    except ValueError as e:
                        print("错误，请输入正确的选项:")
                        InputNum = 0
                if InputNum == 1:  # 回复1时重置计数器
                    TryTimes = 0
                    count = 0
                    continue
                elif InputNum == 2:  # 回复2时跳出整个wihle结束程序
                    Logfile.close()
                    sys.exit(0)
            else:
                if count == 0:
                    print('正在获取板卡型号及机框，请稍候')
                    count = 1
                elif 0 < count < 4:
                    print('.', end="")
                    count = count + 1
                elif count == 4:
                    print('\r', end="")
                    count = 1
                    TryTimes += 1
                time.sleep(1)
                TryTimes += 1
                continue
        # 查询板卡型号、状态并配置

        Logfile.close()
        # 串口通信
    except Exception as e:
        print(e)
        print(traceback.print_exc())
# 打开串口
