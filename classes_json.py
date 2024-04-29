import json

#UTF-8

#Specify the path to your JSON file
json_path = "1_CLASSES/process.json"

#Open and read the JSON file
with open(json_path, 'r') as file:
    json_data = file.read()

#Parse the JSON data into a Python object
data = json.loads(json_data)

#Utilize the data for UML purposes
#Print the data to inspect its structure

#print(data) --> controllare

#Creation of class Activity that refers to CulturalObject
class Activity:
    def _init_(self, institute: str, person: str= None, tool: str|set[str]|None = None, start: str = None, end: str = None):
        super().__init__(id)  #cosi facendo vado a richiamare l'ID della classe IdentifiableEntity
        if not isinstance(institute, str):
            raise ValueError("Institute must be a string for the Activity")
        if person is not None and not isinstance(person, str):
            raise ValueError("Person must be a string or None for the Activity")
        if not isinstance(tool, str, set[str]):
            raise ValueError("Tool must be a string or a set of strings for the Activity")
        if start is not None and not isinstance(start, str):
            raise ValueError("Start Date must be a string or None for the Activity")
        if end is not None and not isinstance(start, str):
            raise ValueError("End Date must be a string or None for the Activity")
        self.institute = institute
        self.person = person
        self.tool = {}
        self.start = start
        self.end = end
        
    def getResponsibleInstitute(self):
        return self.responsibleInstitute
    
    def getResponsiblePerson(self):
        return self.responsiblePerson

    def getTools(self):
        return self.tools
    
    def getStartDate(self):
        return self.startDate 
    
    def getEndDate(self):
        return self.endDate
    
    def refersTo(self, CulturalObject):
        if isinstance(CulturalObject, CulturalObject):
            self.title.append(CulturalObject)
        else:
            raise ValueError("Invalid object type provided")

#Subclass of Activity just with technique parameter

class Acquisition(Activity):
    def _init_(self, technique: str):
        super().__init__(technique) 
        if not isinstance(technique, str):
            raise ValueError("Acquisition.technique must be a string")
        
    def getTechnique(self):
        return self.technique

#Subclasses without defined parameters
class Processing(Activity):
    pass
        
class Modelling(Activity):
    pass

class Optimising(Activity):
    pass

class Exporting(Activity):
    pass
