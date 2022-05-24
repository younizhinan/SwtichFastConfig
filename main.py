import re
import serial.tools.list_ports
import traceback
import time
from _datetime import datetime
import sys


bps = 9600
timex = 0.5
count = 0
SerRead = ''
PonArr = ['32', '24', '16', '16', '8']  # PON口数量，对应CardList列表
PonList = ["16", "16"], \
          ["16", "8"], \
          ["16"], \
          ["8", "8"], \
          ["8"]                         # PON口数量列表，对应CardList列表中的不同型号板卡
CardList = ["1ETGH", "2ETGH", "3PRAM", "4SMXA"], \
           ["1ETGH", "2ETGO", "3PRAM", "4SMXA"], \
           ["1ETGH", "3PRAM", "4SMXA"], \
           ["1ETGO", "2ETGO", "3PRAM", "4SMXA"], \
           ["1ETGO", "3PRAM", "4SMXA"]  # 初始化板卡型号列表
TryTimes = 0
CardType = ""
inputdata = ""
port_list = list(serial.tools.list_ports.comports())  # 获取当前可用串口列表


class OltSerCon():

    def __init__(self, Oltmodel:str, Serial:str):
        self.Oltmodel = Oltmodel
        self.Serial = Serial
        self.now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.filename = ".\\Logs\\" + self.now + ".txt"
        self.Logfile = open(self.filename, 'w', encoding="gbk")

    def LogWrite(self, words:str, endwith:str):  #向日志文件写入
        self.now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.Logfile.write(str(self.Oltmodel))
        self.Logfile.write("-")
        self.Logfile.write(self.now)
        self.Logfile.write(":")
        self.Logfile.write(str(words))
        self.Logfile.write(str(endwith))

    def SerWrite(self, inputdata):  # 向串口写入并计入日志
        self.inputdata = inputdata
        self.Serial.write(inputdata.encode("gbk"))
        self.LogWrite("-->", "\n")
        self.LogWrite(inputdata, "")

    def ReadFormSerial(self):
        self.Readstr = self.Serial.readlines(self.Serial.in_waiting)
        self.LogWrite("<--", "\n")
        for i in self.Readstr:
            self.LogWrite(str(i), "\n")
        return self.Readstr


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
    if len(port_list) == 0:
        print("无可用串口")
        # Log
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
        OltSerCon.LogWrite("There is no Serial can be used.", "\n")
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
    else:
        for i in range(0, len(port_list)):
            print(port_list[i], " .......... ", i + 1)
            # Log
            LogInput = str(port_list[i]) + " .......... " + str(i + 1)
    print("请选择串口:")
    SelectSerial = input()
    # 选择串口

    # 打开串口
    while len(SelectSerial) == 0:
        SelectSerial = input()
    try:
        portx = str(port_list[int(SelectSerial) - 1])
        ZTEser = serial.Serial(portx[0:5], bps, timeout=timex)
        OltSerCon = OltSerCon("C320", ZTEser) # 初始化串口控制类，型号为C320，串口为被选串口
        # Log
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
        LogInput = "Option " + SelectSerial + " has been chosen"
        OltSerCon.LogWrite(LogInput, "\n")
        OltSerCon.LogWrite("Serial detailed parameters:", "\n")
        OltSerCon.LogWrite(str(ZTEser), "\n")
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
        # 串口通信

        # 串口登录
        OltSerCon.SerWrite("\n")
        SerRead = OltSerCon.ReadFormSerial()
        count = 0
        while not IsInList("ZXAN(config)#", SerRead):
            if IsInList("RETURN", SerRead):
                OltSerCon.SerWrite("\n")
                SerRead = OltSerCon.ReadFormSerial()
            elif IsInList("ZXAN>", SerRead):
                OltSerCon.LogWrite("<--ZXAN>", "\n")
                OltSerCon.SerWrite("enable\n")
                SerRead = OltSerCon.ReadFormSerial()
            elif IsInList("Password:", SerRead):
                OltSerCon.LogWrite("<--Password:", "\n")
                OltSerCon.SerWrite("zxr10\n")
                SerRead = OltSerCon.ReadFormSerial()
            elif IsInList("ZXAN#", SerRead):
                OltSerCon.SerWrite("config terminal\n")
                SerRead = OltSerCon.ReadFormSerial()
            elif IsInList("=>", SerRead):
                OltSerCon.SerWrite("boot\n")
                SerRead = OltSerCon.ReadFormSerial()
            else:
                OltSerCon.SerWrite("\n")
                SerRead = OltSerCon.ReadFormSerial()
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
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
        OltSerCon.LogWrite("Login succeed!", "\n")
        OltSerCon.LogWrite("###############SysInfo###############", "\n")
        # 串口登录

        # 查询板卡型号、状态
        count = 0
        TryTimes = 0
        while True:
            OltSerCon.SerWrite("show card\n")
            SerRead = OltSerCon.ReadFormSerial()
            CardType = GetCardType(CardList, SerRead)
            if CardType >= 0:
                print("\r板卡型号获取成功，当前设备PON口数量为:", PonArr[CardType])  # 板卡型号获取成功，开始获取板卡状态
                # Log
                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                LogInput = "CardType is: " + str(CardList[CardType])
                OltSerCon.LogWrite(LogInput, "\n")
                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                # Log
                count = 0
                while True:
                    OltSerCon.SerWrite("show card\n")
                    SerRead = OltSerCon.ReadFormSerial()
                    IsCardRdy(SerRead, CardType)
                    if IsCardRdy(SerRead, CardType):  # 板卡进入INSERVICE状态，开始进行配置
                        print("\r板卡启动成功!正在进行配置...")
                        # Log
                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                        OltSerCon.LogWrite("Card is now in INSERVICE state!", "\n")
                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                        # Log
                        for i in range(0, len(PonList[CardType])):  # 开启PON口
                            for j in range(1, int(PonList[CardType][i]) + 1):
                                inputdata = "interface epon-olt_1/" + str(i + 1) + "/" + str(j) + "\n"
                                OltSerCon.SerWrite(inputdata)
                                OltSerCon.SerWrite("no shutdown\n")
                                OltSerCon.SerWrite("exit\n")
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
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    LogInput = str(VLAN) + " is input,it's an illegal VLAN. VLAN has been reset as '0'."
                                    OltSerCon.LogWrite(LogInput, "\n")
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    VLAN = 0
                            except IndexError as e:
                                print("错误，请输入正确VLAN号:")
                                # Log
                                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                OltSerCon.LogWrite("Wrong Value has been input. VLAN has been reset as '0'.", "\n")
                                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                VLAN = 0
                            except ValueError as e:
                                print("错误，请输入正确VLAN号:")
                                # Log
                                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                OltSerCon.LogWrite("Wrong Value has been input. VLAN has been reset as '0'.", "\n")
                                OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                VLAN = 0
                        inputdata = "vlan " + str(VLAN) + "\n"
                        OltSerCon.SerWrite(inputdata)
                        OltSerCon.SerWrite("description MNG\n")
                        OltSerCon.SerWrite("exit\n")
                        # Log
                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                        LogInput = "Manage VLAN is: " + str(VLAN)
                        OltSerCon.LogWrite(LogInput, "\n")
                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
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
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    LogInput = str(IP) + " is input,it's an illegal IP. IP has been reset as None."
                                    OltSerCon.LogWrite(LogInput, "\n")
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    IP = ''
                                else:
                                    if len(IP) != len(m.group(0)):  # 判断输入的字符串和正则匹配到的是否一致，确保精准匹配
                                        print("请输入正确格式的IP地址:")
                                        # Log
                                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                        LogInput = str(IP) + " is input,it's an illegal IP. IP has been reset as None."
                                        OltSerCon.LogWrite(LogInput, "\n")
                                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
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
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    LogInput = str(Mask) + " is input,it's an illegal Mask. Mask has been reset as None."
                                    OltSerCon.LogWrite(LogInput, "\n")
                                    OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                    Mask = ''
                                else:
                                    if len(Mask) != len(m.group(0)):  # 判断输入的字符串和正则匹配到的是否一致，确保精准匹配
                                        print("请输入正确格式的掩码:")
                                        # Log
                                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                        LogInput = str(Mask) + " is input,it's an illegal Mask. Mask has been reset as None."
                                        OltSerCon.LogWrite(LogInput, "\n")
                                        OltSerCon.LogWrite("###############SysInfo###############", "\n")
                                        Mask = ''
                                    else:
                                        Mask = m.group(0)
                            except Exception as e:
                                print(e)
                        inputdata = "interface vlan " + str(VLAN) + "\n"
                        OltSerCon.SerWrite(inputdata)
                        inputdata = "ip add " + IP + " " + Mask + "\n"
                        OltSerCon.SerWrite(inputdata)
                        OltSerCon.SerWrite("exit\n")

                        # 配置用户名密码
                        OltSerCon.SerWrite("service password-encryption\n")
                        OltSerCon.SerWrite("username wasu password wasu@123 privilege 15\n")
                        OltSerCon.SerWrite("username wasu password wasu@123 max-sessions 16\n")
                        OltSerCon.SerWrite("no ssh server only\n")

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
                        OltSerCon.SerWrite(inputdata)

                        # 配置上联口
                        OltSerCon.SerWrite("interface gei_1/4/1\n")
                        OltSerCon.SerWrite("no shutdown\n")
                        OltSerCon.SerWrite("switchport mode trunk\n")
                        inputdata = "switchport vlan " + str(VLAN) + " tag\n"
                        OltSerCon.SerWrite(inputdata)
                        OltSerCon.SerWrite("exit\n")
                        OltSerCon.SerWrite("exit\n")
                        OltSerCon.SerWrite("write\n")
                        print("配置完成!")

                        OltSerCon.Logfile.close()
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
                    OltSerCon.Logfile.close()
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

        OltSerCon.Logfile.close()
        # 串口通信
    except Exception as e:
        print(e)
        print(traceback.print_exc())
# 打开串口
