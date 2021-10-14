class ObjectData:
    def __init__(self, name, address, categories, time, url):         
        self.name = name
        self.address = address
        self.categories = categories
        self.time = time
        self.url = url

    def getName(self):        
        return self.name
     
    def getAddress(self):        
        return self.address
     
    def getCategories(self):        
        return self.categories
     
    def getTime(self):        
        return self.time
     
    def getUrl(self):        
        return self.url

    def buildMinInfo(self):
        return self.name + ": " + self.address

    def buildAllInfo(self):
        str = self.name + ": " + self.address + "\n"
        for category in self.categories:
            str = str + category + "/"
        str = str + "\n"
        if self.time is not None:
            str = str + self.time  + "\n"
        if self.url is not None:
            str = str + self.url  + "\n"
        return str