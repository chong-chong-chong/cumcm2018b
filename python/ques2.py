import time

time_start=time.time()

class workpiece:
    ID = 0
    stage = 0

    def __init__(self,ID):
        self.ID = ID
        self.stage = 0

    def NextStage(self):
        self.stage += 1

class CNC:
    '''
    working     状态
    True        加工
    False       等待上下料
    '''
    workpieceOn = None
    tool = 0
    mechNum = 1
    working = False
    restTime = 0
    workingTime = 0
    goingToStop = False
    on = True

    def __init__(self,mechNum,tool,workingTime):
        self.mechNum = mechNum
        self.state = 0
        self.tool = tool
        self.workingTime = workingTime[tool]

    def off(self):
        self.on = False

    def exit(self):
        self.goingToStop = True

    def timeGoes(self,timeSpan):
        if not(self.working):
            return
        restTime = self.restTime-timeSpan
        if restTime>0:
            self.restTime = restTime
        else:
            self.restTime = 0
            self.working = False #完成
            self.workpieceOn.NextStage()

    def __str__(self):
        if self.tool==1:
            lb = "{"
            rb = "}"
        else:
            lb = "["
            rb = "]"
        tab = '\t'
        if self.working:
            return lb+tab+self.restTime.__str__()+tab+rb
        else:
            return lb+tab+tab+rb

class RGV:
    '''
    机位说明
                [2]     [4]     [6]     [8]
    Location    <0>     <1>     <2>     <3>
                [1]     [3]     [5]     [7]

    '''
    moveTime = {0:0,1:20,2:33,3:46}
    reloadTime = {1:20,2:33,3:46}
    workpieceOn = workpiece(1)
    cleanTime = 25
    Location = 0
    Destination = 0
    startedNum = 1 #已经投入的工件数目
    finishedNum = 0 #已经成功完成的工件数目
    goingToStop = False
    def __init__(self,**timeArgs):
        self.Location = 0
        self.moveTime = timeArgs['moveTime']
        self.reloadTime = timeArgs['reloadTime']
        self.cleanTime = timeArgs['cleanTime']
        self.workpieceOn = workpiece(1)
        self.startedNum = 1
        self.finishedNum = 0
        self.goingToStop = False

    def exit(self):
        self.goingToStop = True

    def moveTo(self,Destination):
        self.Location = Destination

    def getNewWorkpiece(self):
        self.startedNum += 1
        nwp = workpiece(self.startedNum)
        self.workpieceOn = nwp
        return nwp
    
    def reloadTo(self,cnc):
        #抓取完成的工件
        workpieceFinished = cnc.workpieceOn
        #上本地工件给CNC
        cnc.workpieceOn = self.workpieceOn
        #更新
        self.workpieceOn = workpieceFinished
        #换上去了什么?
        if cnc.workpieceOn == None:
            pass     
        else:
            #重新上钟!
            cnc.working = True
            cnc.restTime = cnc.workingTime
    
    def clean(self):
        self.finishedNum += 1
        #self.workpieceOn.NextStage
        #如果要下班,拒绝上料
        

    def __str__(self):
        tab = "\t"
        if self.workpieceOn == None:
            ID = " "
            Stage = " "
        else:
            ID = self.workpieceOn.ID.__str__()
            Stage = self.workpieceOn.stage.__str__()
        info = "<"+tab+Stage+tab+">"
        row = ["\t \t","\t \t","\t \t","\t \t"]
        if self.Destination==self.Location:
            row[self.Destination] = "["+info+"]"
        else:
            row[self.Destination] = "\t=> \t"
            row[self.Location] = info
        
        
        return row[0] + tab + row[1] + tab + row[2] + tab + row[3]

    
class streamline:
    '''
    以RGV的动作分段
    机器在完成这个动作后,下一个动作是什么?
    我们希望:
    总等待时间最短
    那么由贪心算法,我们希望这一个动作所带来的等待时间最短

    1.  如果没有CNC等待reload,则到下一个加工完成的CNC去

    2.  如果有一系列 CNC 等待 unload (in waiting_List)
        那么我们 moveTo(i), 直到RGV下一次等待指令时候,总等待时间最小

    3.  对于有两道工序的任务,如果我们取了CNC_list_tool1,waitingList = CNC_list_tool2,不清洗
        如果我们取了CNC_list_tool2,清洗,waitingList = CNC_list_tool1

    4.  如何退出工艺：
        我们希望在下班之前，小车位于原位，并且所有的零件都已经加工完
        当我们取一个新件时，
    '''
    #rgv = RGV()
    CNC_list = {}
    time = 0
    rgv = None
    info = ""
    goingToStop = False
    CNC_list_on = {1,2,3,4,5,6,7,8}
    CNC_list_have = {1,2,3,4,5,6,7,8}
    def __init__(self,tools,**timeArgs):
        '''
        格式:
        tools = {1:1,2:1,3:1,4:1,5:1,6:2,7:2,8:2}
        '''
        self.rgv = RGV(moveTime = timeArgs['moveTime'],reloadTime = timeArgs['reloadTime'],cleanTime = timeArgs['cleanTime'])
        self.CNC_list = {}
        self.CNC_list_tool1 = []
        self.CNC_list_tool2 = []
        for mechNum in range(1,9):
            self.CNC_list[mechNum] = CNC(mechNum,tools[mechNum],timeArgs['workingTime'])
        #装载刀具
        for mechNum in tools:
            if tools[mechNum] == 1:
                self.CNC_list_tool1.append(mechNum)
            elif tools[mechNum] == 2:
                self.CNC_list_tool2.append(mechNum)
            else:
                print("WARING : Wrong Tool Number!!!")
                return
            
        self.time = 0
        self.info = ""
        self.goingToStop = False

    def exit(self):
        self.goingToStop = True
        self.rgv.exit()
        for mechNum in self.CNC_list:
            self.CNC_list[mechNum].exit()

    def CNCtimeGoes(self,timeSpan):
        for mechNum in range(1,9):
            self.CNC_list[mechNum].timeGoes(timeSpan)

    def nextActionGroup(self):
        #八小时以后收工
        if not(self.goingToStop) and self.time>25400:
            self.exit()
        
        #搜索所有CNC,如果找到待取的CNC
        for mechNum in self.CNC_list:
            if not(self.CNC_list[mechNum].workpieceOn==None):
                self.CNC_list_have.add(mechNum)
            else:
                self.CNC_list_have.discard(mechNum)
        if len(self.CNC_list_have) == 0 and self.goingToStop:
            return

        #无新料,退出,等待所有开着的CNC
        if self.rgv.workpieceOn == None:
            waitingList = self.CNC_list_have
        #生料 阶段0 进入tool1
        elif self.rgv.workpieceOn.stage==0:
            waitingList = self.CNC_list_tool1
        #阶段1,送入tool2
        elif self.rgv.workpieceOn.stage==1:
            waitingList = self.CNC_list_tool2
        else:
            pass

        min_Time = 27200
        for mechNum in waitingList:
            cnc = self.CNC_list[mechNum]
            taskTime = max(self.rgv.moveTime[abs((mechNum-1)//2-self.rgv.Location)] , cnc.restTime ) \
                        + self.rgv.reloadTime[mechNum]
            if min_Time>taskTime:
                min_Time = taskTime
                min_mechNum = mechNum

        aimCNC = self.CNC_list[min_mechNum]
        aimLocation = (min_mechNum-1)//2
        #确定目的地
        self.rgv.Destination = aimLocation
        #添加记录
        self.info += self.show()
        #结算时间(下次RGV自由时)
        self.CNCtimeGoes(min_Time)
        self.time += min_Time
        #移动
        self.rgv.moveTo(aimLocation)
        #交换 RGV 和 CNC 的工件
        self.rgv.reloadTo(aimCNC)
        #让我们看看我们从 CNC 上面换下来了什么?
        if self.rgv.workpieceOn == None:
            if not(self.rgv.goingToStop):
                self.rgv.getNewWorkpiece()
        elif self.rgv.workpieceOn.stage == 2:
            #结算清洗时间
            self.CNCtimeGoes(self.rgv.cleanTime)
            self.time += self.rgv.cleanTime
            if not(self.goingToStop):
                self.rgv.getNewWorkpiece()
            else:
                self.rgv.workpieceOn = None
        else:
            pass
    
        #下一次运动
        self.nextActionGroup()

    def start(self):
        self.nextActionGroup()

    def show(self):
        '''
        [O] [X] [O] [O]
            RGV     ->
        [O] [O] [O] [O]
        '''
        tb = "\t"
        time = self.time.__str__()
        text    = self.CNC_list[2].__str__()+tb+self.CNC_list[4].__str__()+tb+self.CNC_list[6].__str__()+tb+self.CNC_list[8].__str__()\
                + "\n" + self.rgv.__str__() + "\n"\
                + self.CNC_list[1].__str__()+tb+self.CNC_list[3].__str__()+tb+self.CNC_list[5].__str__()+tb+self.CNC_list[7].__str__()
        return '\n'+time+'\n'+text+'\n'



N = {}
for i in range(1,255):
    p = bin(i)
    tools = {}
    for num in range(1,9):
        tools[num] = i%2+1
        i = i//2
    LineA = streamline( tools,moveTime = {0:0,1:20,2:33,3:46},\
                                reloadTime = {1:28,3:28,5:28,7:28,2:31,4:31,6:31,8:31},\
                                cleanTime = 25,\
                                workingTime = {1:400,2:378})

    LineA.start()
    N[p] = LineA.rgv.startedNum
key = max(N, key=N.get)
val = N[key]
print(key,val)

'''
tools = {1:1,2:1,3:2,4:1,5:2,6:2,7:1,8:1}
LineA = streamline( tools,moveTime = {0:0,1:20,2:33,3:46},\
                            reloadTime = {1:28,3:28,5:28,7:28,2:31,4:31,6:31,8:31},\
                            cleanTime = 25,\
                            workingTime = {1:400,2:378})
LineA.start()
ft = open('workStream2.txt','w',encoding='utf-8')

ft.write(LineA.info)
ft.close()


print('time cost',time_end-time_start,'s',' ',LineA.rgv.startedNum)
'''
time_end=time.time()