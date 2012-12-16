import time
import random
import os
import threading
import sys


class WebsiteFinder:


    def __init__(self):
        self.startTimeInSec = time.time()  
        startDatePipe = os.popen("date", "r")
        self.startDate = startDatePipe.read()
        startDatePipe.close

        self.fileName = "websites.txt"
        self.file = open(self.fileName, "a", 1)
        self.file.write("\n" + self.startDate)

        self.timeLimitInMin = 0
        self.sitesFound = 0
        self.sitesFoundLimit = sys.maxint
        self.ipsTested = 0

        self.numThreads = 0
        self.threads = []


    def getInput(self):
	print "WebsiteFinder scans random ipv4 addresses and looks for a header"
    	print "that signals a website exits for the address"
    	print ""

        self.timeLimitInMin = float(input("Enter the max runtime(min): "))
        self.sitesFoundLimit = int(input(\
                               "Enter the max amount of websites to find: "))
        self.numThreads = int(input(\
                          "Enter the amount of ip address checking threads: "))
        print ""

    def ipGenerator(self):
        num1 = random.randrange(1,254)
        num2 = random.randrange(1,254)
        num3 = random.randrange(1,254)
        num4 = random.randrange(1,254)

        while num1 == 127:
            num1 = random.randrange(1,254)

        ipAddress = str(num1) + "." + str(num2) + "." + \
                    str(num3) + "." + str(num4)

        return ipAddress


    def testIpForWebsite(self,ipAddress):
        command = "HEAD -t 1 -C bleh:blah " + ipAddress
        headPipe = os.popen(command, "r")
        line = headPipe.readline()
        headPipe.close()

        #print line
        self.ipsTested += 1

        # if HTTP status code  == 2**
        if line[0] == "2":
            self.sitesFound += 1
            return True
        else:
            return False

    
    def findAndWriteWebsites(self):
        while self.getRemainingTime() >0 and self.sitesFound < self.sitesFoundLimit:
            ipAddress = self.ipGenerator()
            
            if self.testIpForWebsite(ipAddress):
                self.file.write(ipAddress + "\n")


    def updateTerminalDisplay(self):
        while self.getRemainingTime() > 0 and self.sitesFound < self.sitesFoundLimit: 
            remainMin = int(self.getRemainingTime() / 60)
            remainSec = self.getRemainingTime() - (remainMin * 60)
            sys.stdout.write("\rRemaining Time: %dm%.0fs    Ips Tested: %d    Websites Found: %d" % (remainMin, remainSec, self.ipsTested, self.sitesFound))
	    sys.stdout.flush()
            time.sleep(1)


    def getRemainingTime(self):
	currentTime = time.time()
        runningTime = currentTime - self.startTimeInSec
        timeLimitInSec = self.timeLimitInMin * 60
        remainingTime = timeLimitInSec - runningTime

        return remainingTime   


    def run(self):
        self.getInput()

        displayThread = threading.Thread(target=self.updateTerminalDisplay)
        displayThread.start()

        for n in range(self.numThreads):
	    thread = threading.Thread(target=self.findAndWriteWebsites)
	    thread.start()
            self.threads.append(thread)

        displayThread.join()

        sys.stdout.write("\n")

        for thread in self.threads:
            thread.join()

        self.file.close()

        print ""


def main():
    siteFinder = WebsiteFinder()
    siteFinder.run()


if __name__ == "__main__":
    main()
