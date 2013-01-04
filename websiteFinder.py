import time
import random
import threading
import sys
import httplib
import json

class WebsiteFinder:

    def __init__(self):
        self.startTimeInSec = time.time()
        self.date = time.strftime("%a %b %d %H:%M:%S %Z %Y")
        
        settingsFile = open("settings.json")
        self.settings = json.load(settingsFile)

        self.fileName = self.settings["outputFilename"]
        self.file = open(self.fileName, "a", 1)
        self.file.write("\n" + self.date + "\n")
        
        self.numThreads = self.settings["testingThreads"]
        self.connTimeout = self.settings["connectionTimeout"]
        self.timeLimitInSec = self.getTimeLimitInSec()            
        self.sitesFound = 0
        self.sitesFoundLimit = self.settings["runtimeLimits"]["sitesFound"]
        self.adresTested = 0
        self.adresTestLimit = self.settings["runtimeLimits"]["addressesTested"]


    def getTimeLimitInSec(self):
        timeLimits = self.settings["runtimeLimits"]["time"]
        
        # using list with timeLimits dict values embedded because for loop 
        # requires ordered structure
        limitValues = []
        limitValues.append(timeLimits["hour"])
        limitValues.append(timeLimits["minute"])
        limitValues.append(timeLimits["second"])
        
        timeLimitInSec = 0
        valueSecs = 60**2
        
        for value in limitValues:
            if value != None:
                timeLimitInSec += (value * valueSecs)
            valueSecs /= 60    
            
        return timeLimitInSec
    

    def limited(self):
        runtimeLimits = self.settings["runtimeLimits"]
        
        IsItNone = []
        for value in runtimeLimits["time"].values():
            if value == None:
                IsItNone.append(True)
            else:
                IsItNone.append(False)
        
        timeLimited = any(IsItNone) != True 
        sitesFoundLimited = runtimeLimits["sitesFound"] != None
        adresTestLimited = runtimeLimits["addressesTested"] != None
    
        if ((timeLimited and self.getRemainingTime() < 0) or
            (sitesFoundLimited and self.sitesFound > self.sitesFoundLimit) or
            (adresTestLimited and self.adresTested > self.adresTestLimit)):
                return True
        else:
            return False


    def ipGenerator(self):
        num1 = random.randrange(1,254)
        num2 = random.randrange(1,254)
        num3 = random.randrange(1,254)
        num4 = random.randrange(1,254)

        while num1 in [127, 10]:
            num1 = random.randrange(1,254)
         
        while ((num1 == 192 and num2 == 168) or 
               (num1 == 172 and num2 in range(16,32))):
            num1 = random.randrange(1,254)
            num2 = random.randrange(1,254)
            
        ipAddress = str(num1) + "." + str(num2) + "." + \
                    str(num3) + "." + str(num4)

        return ipAddress


    def testAdresForWebsite(self,ipAddress):
        self.adresTested += 1
        
        try:
            conn = httplib.HTTPConnection(ipAddress, timeout=self.connTimeout)
            conn.request("HEAD", "/")
            response = conn.getresponse()
            status = response.status

            if status == 200:
                self.sitesFound += 1
                return True
            else:
                return False

        # returns false for all exceptions, should write exceptions to log file
        # and should check if there is any internet connection
        except(Exception):
            return False

    
    def findAndWriteWebsites(self):
        while not self.limited():
            ipAddress = self.ipGenerator()
            
            if self.testAdresForWebsite(ipAddress):
                self.file.write(ipAddress + "\n")


    def updateTerminalDisplay(self):
        while not self.limited():
            totalSeconds = self.getRemainingTime()
            hour, min, sec = self.secsToHrMinSec(totalSeconds)
            # when there is no time limit shows a negative time
            # should display null when there is no time limit            
            sys.stdout.write("\rRemaining Time: %dh% dm% ds    Adres Tested: %d    Websites Found: %d   " % (hour, min, sec, self.adresTested, self.sitesFound))
     	    sys.stdout.flush()
            time.sleep(1)
    
    
    def secsToHrMinSec(self, seconds):
        secs = seconds
        minutes, seconds = divmod(secs, 60)
        hours, minutes = divmod(minutes, 60)
        return hours, minutes, seconds
        

    def getRemainingTime(self):
        currentTime = time.time()
        runningTime = currentTime - self.startTimeInSec
        remainingTime = self.timeLimitInSec - runningTime

        return remainingTime   


    def run(self):
        hour, min, sec = self.secsToHrMinSec(self.timeLimitInSec)
        print "Time Limit: %dh %dm %ds" % (hour, min, sec)
        
        threads = []
        displayThread = threading.Thread(target=self.updateTerminalDisplay)
        displayThread.start()

        for n in range(self.numThreads):
	        thread = threading.Thread(target=self.findAndWriteWebsites)
	        thread.start()
	        threads.append(thread)

        displayThread.join()

        sys.stdout.write("\n")

        for thread in threads:
            thread.join()

        self.file.close()

        print ""


def main():
    siteFinder = WebsiteFinder()
    siteFinder.run()


if __name__ == "__main__":
    main()
