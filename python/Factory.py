class CNC:
    '''
    working     状态
    True        加工
    False       等待上下料
    '''
    mechNum = 1
    working = False
    restTime = 0
    workingTime = 0
    def __init__(self,mechNum,workingTime):
        self.mechNum = mechNum
        self.state = 0
        self.workingTime = workingTime
    def timeGoes(self,timeSpan):
        if not(self.working):
            return
        restTime = self.restTime-timeSpan
        if restTime>0:
            self.restTime = restTime
        else:
            self.restTime = 0
            self.working = False #完成

    def __str__(self):
        tab = '\t'
        if self.working:
            return "["+tab+self.restTime.__str__()+tab+"]"
        else:
            return "[\t\t]"

class RGV:
    '''
    机位说明
                [2]     [4]     [6]     [8]
    Location    <0>     <1>     <2>     <3>
                [1]     [3]     [5]     [7]

    '''
    moveTime = {0:0,1:20,2:33,3:46}
    reloadTime = {1:20,2:33,3:46}
    cleanTime = 25
    Location = 0
    Destination = 0
    finishedNum = 0

    def __init__(self,**timeArgs):
        self.Location = 0
        self.moveTime = timeArgs['moveTime']
        self.reloadTime = timeArgs['reloadTime']
        self.cleanTime = timeArgs['cleanTime']

    
    def moveTo(self,Destination):
        self.Location = Destination
    
    def reloadTo(self,cnc):
        cnc.working = True
        cnc.restTime = cnc.workingTime
        #重新上钟!

    def clean(self):
        self.finishedNum += 1

    def __str__(self):
        row = ["\t \t","\t \t","\t \t","\t \t"]
        if self.Destination==self.Location:
            row[self.Destination] = "[\t·\t]"
        else:
            row[self.Destination] = "\t=> \t"
            row[self.Location] = "\trgv\t"
        
        tab = "\t"
        return row[0] + tab + row[1] + tab + row[2] + tab + row[3]

    
class streamline:
    '''
    以RGV的动作分段
    机器在完成这个动作后,下一个动作是什么?
    我们希望:
    总等待时间最短
    那么由贪心算法,我们希望这一个动作所带来的等待时间最短

    1.  如果没有CNC等待unload,则到下一个加工完成的CNC去

    2.  如果有一系列 CNC 等待 unload (in waiting_List)
        那么我们 moveTo(i), 直到RGV下一次等待指令时候,总等待时间最小
        argmin( moveTo(i) + unloadTo(CNC_list[i-1]) + clean() )
    '''
    #rgv = RGV()
    CNC_list = {}
    time = 0
    CNCserving = []
    rgv = 0
    info = ""
    def __init__(self,**timeArgs):
        self.rgv = RGV(moveTime = timeArgs['moveTime'],reloadTime = timeArgs['reloadTime'],cleanTime = timeArgs['cleanTime'])
        self.CNC_list = {}
        for mechNum in range(1,9):
            self.CNC_list[mechNum] = CNC(mechNum,timeArgs['workingTime'])
        self.time = 0
        self.info = ""

    def CNCtimeGoes(self,timeSpan):
        for mechNum in range(1,9):
            self.CNC_list[mechNum].timeGoes(timeSpan)

    def nextActionGroup(self):
        if self.time>8*60*60:
            print("Finished",self.rgv.finishedNum)
            return

        min_Time = 0
        for mechNum in range(1,9):
            cnc = self.CNC_list[mechNum]
            taskTime = max(self.rgv.moveTime[abs((mechNum-1)//2-self.rgv.Location)] , cnc.restTime ) \
                        + self.rgv.reloadTime[mechNum] \
                        + self.rgv.cleanTime
            if mechNum == 1 or min_Time>taskTime:
                min_Time = taskTime
                min_mechNum = mechNum
        self.rgv.Destination = (min_mechNum-1)//2
        self.info += self.show()
        self.rgv.moveTo((min_mechNum-1)//2)
        #移动到目标位置
        #依据策略,就算没有加工完成,也会等待加工完成
        self.rgv.reloadTo(self.CNC_list[min_mechNum])
        self.rgv.clean()
        self.CNCtimeGoes(min_Time)
        #完成一套,结算时间
        self.time += min_Time
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



LineA = streamline( moveTime = {0:0,1:20,2:33,3:46},\
                            reloadTime = {1:28,3:28,5:28,7:28,2:31,4:31,6:31,8:31},\
                            cleanTime = 25,\
                            workingTime = 560)

LineA.start()
ft = open('workStream.txt','w',encoding='utf-8')
ft.write(LineA.info)
ft.close()

