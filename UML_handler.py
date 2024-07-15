from rdflib import Graph, URIRef, RDF, Namespace, Literal
from rdflib.namespace import FOAF
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore
from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import csv
import json
from UML_classes import Acquisition, Processing, Modelling, Optimising, Exporting
from sparql_dataframe import get
from typing import Optional, List, Any, Dict
from pandas import Series
from sqlite3 import connect


class Handler(object):  # Chiara
    def __init__(self):
        self.dbPathOrUrl = ""

    def getDbPathOrUrl(self):
        return self.dbPathOrUrl

    def setDbPathOrUrl(self, pathOrUrl: str) -> bool:
        self.dbPathOrUrl = pathOrUrl
        return self.dbPathOrUrl == pathOrUrl

class UploadHandler(Handler):
    def __init__(self):
        super().__init__()

    def pushDataToDb(self, path):
        pass

class MetadataUploadHandler(UploadHandler):  # Chiara
    def __init__(self):
        self.dbPathOrUrl = ""

    def pushDataToDb(self, path) -> bool:

            my_graph = Graph()
            # Read the data from the csv file and store them into a dataframe
            venus = pd.read_csv(path,
                                keep_default_na=False,
                                dtype={
                                    "Id": "string",
                                    "Type": "string",
                                    "Title": "string",
                                    "Date": "string",
                                    "Author": "string",
                                    "Owner": "string",
                                    "Place": "string",
                                })
            # Rimuoviamo i duplicati della colonna id, mantenendo la prima istanza
            venus.drop_duplicates(subset=["Id"], keep="first", inplace=True, ignore_index=True)

            # Define namespaces
            base_url = Namespace("http://github.com/HelloKittyDataClan/DSexam/")
            db = Namespace("https://dbpedia.org/property/")
            schema = Namespace("http://schema.org/")

            # Create Graph
            my_graph.bind("base_url", base_url)
            my_graph.bind("db", db)
            my_graph.bind("FOAF", FOAF)
            my_graph.bind("schema", schema)

            # Define classes about Cultural Object
            Person = URIRef(FOAF + "Person")
            NauticalChart = URIRef(base_url + "NauticalChart")
            ManuscriptPlate = URIRef(base_url + "ManuscriptPlate")
            ManuscriptVolume = URIRef(base_url + "ManuscriptVolume")
            PrintedVolume = URIRef(base_url + "PrintedVolume")
            PrintedMaterial = URIRef(base_url + "PrintedMaterial")
            Herbarium = URIRef(db + "Herbarium")
            Specimen = URIRef(base_url + "Specimen")
            Painting = URIRef(db + "Painting")
            Model = URIRef(db + "Model")
            Map = URIRef(db + "Map")

            # Attributes related to classes
            title = URIRef(schema + "title")
            date = URIRef(schema + "dateCreated")
            place = URIRef(schema + "itemLocation")
            id = URIRef(schema + "identifier")
            owner = URIRef(base_url + "owner")

            # Relation with authors among classes
            relAuthor = URIRef(schema + "author")

            # Attributes related to the class Person
            name = URIRef(FOAF + "name")  # URI di FOAF http://xmlns.com/foaf/0.1/

            # Add to the graph the Cultural Object
            for idx, row in venus.iterrows():
                loc_id = "culturalobject-" + str(idx)
                subj = URIRef(base_url + loc_id)
                if row["Id"] != "":
                    my_graph.add((subj, id, Literal(str(row["Id"]))))

                # Assign a resource class to the object
                if row["Type"] != "":
                    if row["Type"].lower() == "nautical chart":
                        my_graph.add((subj, RDF.type, NauticalChart))
                    elif row["Type"].lower() == "manuscript plate":
                        my_graph.add((subj, RDF.type, ManuscriptPlate))
                    elif row["Type"].lower() == "manuscript volume":
                        my_graph.add((subj, RDF.type, ManuscriptVolume))
                    elif row["Type"].lower() == "printed volume":
                        my_graph.add((subj, RDF.type, PrintedVolume))
                    elif row["Type"].lower() == "printed material":
                        my_graph.add((subj, RDF.type, PrintedMaterial))
                    elif row["Type"].lower() == "herbarium":
                        my_graph.add((subj, RDF.type, Herbarium))
                    elif row["Type"].lower() == "specimen":
                        my_graph.add((subj, RDF.type, Specimen))
                    elif row["Type"].lower() == "painting":
                        my_graph.add((subj, RDF.type, Painting))
                    elif row["Type"].lower() == "model":
                        my_graph.add((subj, RDF.type, Model))
                    elif row["Type"].lower() == "map":
                        my_graph.add((subj, RDF.type, Map))

                # Assign title
                if row["Title"] != "":
                    my_graph.add((subj, title, Literal(str(row["Title"]))))
                # Assign date
                if row["Date"] != "":
                    my_graph.add((subj, date, Literal(str(row["Date"]))))
                # Assign owner
                if row["Owner"] != "":
                    my_graph.add((subj, owner, Literal(str(row["Owner"]))))
                # Assign place
                if row["Place"] != "":
                    my_graph.add((subj, place, Literal(str(row["Place"]))))

            # Populating the graph with all the people
            author_id_mapping = dict()
            object_mapping = dict()
            people_counter = 0

            for idx, row in venus.iterrows():
                if row["Author"] != "":
                    author_list = row["Author"].split(";")
                    for author in author_list:
                        if "(" in author and ")" in author:
                            split_index = author.index("(")
                            author_name = author[:split_index - 1].strip()
                            author_id = author[split_index + 1:-1].strip()

                            object_id = row["Id"]

                            if author_id in author_id_mapping:
                                person_uri = author_id_mapping[author_id]
                            else:
                                local_id = "person-" + str(people_counter)
                                person_uri = URIRef(base_url + local_id)
                                my_graph.add((person_uri, RDF.type, Person))
                                my_graph.add((person_uri, id, Literal(author_id)))
                                my_graph.add((person_uri, name, Literal(author_name)))
                                author_id_mapping[author_id] = person_uri
                                people_counter += 1

                            if object_id in object_mapping:
                                object_mapping[object_id].add(person_uri)
                            else:
                                object_mapping[object_id] = {person_uri}

                # Aggiungi l'assegnazione degli autori al grafo
                for object_id, authors in object_mapping.items():
                    for author_uri in authors:
                        my_graph.add((URIRef(base_url +"culturalobject-" + object_id), relAuthor, author_uri))  # MODIFICA!!! mancava culturalheritageobject come parte del predicato

            # Store RDF data in SPARQL endpoint
            store = SPARQLUpdateStore()
            endpoint = self.getDbPathOrUrl() + "sparql"
            store.open((endpoint, endpoint))  # First parameter reading data, second write database

            for triple in my_graph.triples((None, None, None)):
                store.add(triple)

            store.close()

            # Verificare se il grafo è stato caricato 
            query_graph = """
            SELECT ?s ?p ?o
            WHERE {
                ?s ?p ?o .
            }
            """
            result_dataset = get(endpoint, query_graph, True)

            num_triples_blazegraph = len(result_dataset)
            num_triples_local = len(my_graph)

            pos = num_triples_blazegraph == num_triples_local
            if pos:
                print("I dati sono stati caricati con successo su Blazegraph.")
                return True
            else:
                print("Caricamento dei dati su Blazegraph non riuscito.")
                return False


'''prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix schema: <http://schema.org/>
prefix FOAF: <http://xmlns.com/foaf/0.1/>
       

SELECT ?culturalObjectURI ?culturalObjectId
WHERE {
            ?culturalObjectURI rdf:type ?type .
            FILTER(?type != FOAF:Person)
            ?culturalObjectURI schema:identifier ?culturalObjectId .
        }'''


#---------------------------

# Define the data type for lists of dictionaries
DataType = List[Dict[str, Any]]

# qui c'era class Handler(object):  # Chiara e class UploadHandler(Handler)
# ma non so sto datatype qi sopra dove deve andare


#_____________________RELATIONAL DATA BASE____________________________

class ProcessDataUploadHandler(UploadHandler):  #Cata
    def __init__(self):
        super().__init__()

    #Create data frame with the objects ID beacuse activities refers to. (Data Frame is a function that allows us to create kind of tables with pandas)
    def pushDataToDbObject(self, file_path: str) -> pd.DataFrame:
        cultural_objects = pd.read_csv(file_path, keep_default_na=False,
                            dtype={
                                "Id": "string", 
                                "Type": "string", 
                                "Title": "string",
                                "Date": "string", 
                                "Author": "string", 
                                "Owner": "string",
                                "Place": "string"})
        
        objects_ids = cultural_objects[["Id"]]
        objects_internal_ids = ["object-" + str(idx) for idx in range(len(objects_ids))]
        objects_ids.insert(0, "objectId", pd.Series(objects_internal_ids, dtype="string"))
        
        objects_ids_df = pd.DataFrame(objects_ids)
        objects_ids_df.to_csv('objects_ids.csv', index=False)
        
        return objects_ids_df

    #Create a function to create 5 different tables
    def pushDataToDbActivities(self, file_path: str, field_name: str) -> pd.DataFrame:
        # Load JSON data from file
        with open(file_path, 'r') as file:
            df_activity = json.load(file)
        
        table_data: List[Dict[str, Any]] = []
        
        for item in df_activity:
            if field_name in item:
                field_entry = item[field_name]
                field_entry['object id'] = item['object id']
                table_data.append(field_entry)

        # Convert the list of dictionaries to a DataFrame
        df_activities = pd.DataFrame(table_data)
        
        # Convert lists in 'tool' column to comma-separated strings because lists are not readed
        if 'tool' in df_activities.columns:
            df_activities['tool'] = df_activities['tool'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)
            
        return df_activities

    #Create internalId for each one (important for queries)
    def addInternalIds(self, df: pd.DataFrame, field_name: str) -> pd.DataFrame:
        # Create internal IDs
        internal_ids = [f"{field_name}-{idx}" for idx in range(len(df))]
        # Add the internal IDs as a new column
        df.insert(0, "internalId", Series(internal_ids, dtype="string"))
        
        return df
    
    # Function to join activities with objects based on object id (to guarantee that the activities are connected with the objects)
    def joinActivitiesWithObjects(self, df_activities: pd.DataFrame, objects_ids_df: pd.DataFrame, left_on: str, right_on: str) -> pd.DataFrame:
        return pd.merge(df_activities, objects_ids_df, left_on=left_on, right_on=right_on, how="left")

    #Replace object id with objectId (internal id of objects). Two cases with the row technique included (activities) or without this data
    def extractAndRenameColumns(self, df: pd.DataFrame, include_technique: bool = False) -> pd.DataFrame:
        columns = ["internalId", "object id", "responsible institute", "responsible person", "tool", "start date", "end date"]
        if include_technique:
            columns.insert(4, "technique")  # Insert 'technique' column before 'tool'
        
        identifiers = df[columns]
        identifiers = identifiers.rename(columns={"object id": "objectId"})
        return identifiers
        
    #Create individual DataFrame tables calling the pushDataToDbActivities, internal ID, etc.
    def createTablesActivity(self, activities_file_path: str, objects_file_path: str):
        #Create individual DataFrames
        acquisition_df = self.pushDataToDbActivities(activities_file_path, 'acquisition')
        processing_df = self.pushDataToDbActivities(activities_file_path, 'processing')
        modelling_df = self.pushDataToDbActivities(activities_file_path, 'modelling')
        optimising_df = self.pushDataToDbActivities(activities_file_path, 'optimising')
        exporting_df = self.pushDataToDbActivities(activities_file_path, 'exporting')

        #Add internal IDs to each DataFrame
        acquisition_df = self.addInternalIds(acquisition_df, 'acquisition')
        processing_df = self.addInternalIds(processing_df, 'processing')
        modelling_df = self.addInternalIds(modelling_df, 'modelling')
        optimising_df = self.addInternalIds(optimising_df, 'optimising')
        exporting_df = self.addInternalIds(exporting_df, 'exporting')

        #Load object IDs
        objects_ids_df = self.pushDataToDbObject(objects_file_path)

        #Join activity DataFrames with objects DataFrame
        acquisition_joined = self.joinActivitiesWithObjects(acquisition_df, objects_ids_df, "object id", "objectId")
        processing_joined = self.joinActivitiesWithObjects(processing_df, objects_ids_df, "object id", "objectId")
        modelling_joined = self.joinActivitiesWithObjects(modelling_df, objects_ids_df, "object id", "objectId")
        optimising_joined = self.joinActivitiesWithObjects(optimising_df, objects_ids_df, "object id", "objectId")
        exporting_joined = self.joinActivitiesWithObjects(exporting_df, objects_ids_df, "object id", "objectId")

        #Extract and rename columns, including 'technique' for acquisition
        acquisition_final_db = self.extractAndRenameColumns(acquisition_joined, include_technique=True)
        processing_final_db = self.extractAndRenameColumns(processing_joined)
        modelling_final_db = self.extractAndRenameColumns(modelling_joined)
        optimising_final_db = self.extractAndRenameColumns(optimising_joined)
        exporting_final_db = self.extractAndRenameColumns(exporting_joined)
        
        #Save to SQLite database in the file
        with connect("activities.db") as con:
            objects_ids_df.to_sql("ObjectId", con, if_exists="replace", index=False)
            acquisition_final_db.to_sql("Acquisition", con, if_exists="replace", index=False)
            processing_final_db.to_sql("Processing", con, if_exists="replace", index=False)
            modelling_final_db.to_sql("Modelling", con, if_exists="replace", index=False)
            optimising_final_db.to_sql("Optimising", con, if_exists="replace", index=False)
            exporting_final_db.to_sql("Exporting", con, if_exists="replace", index=False)


#How to implement the code (example):
'''process_upload = ProcessDataUploadHandler()
process_upload.createTablesActivity('data/process.json', 'data/meta.csv')'''

class QueryHandler(Handler):
    def __init__(self, dbPathOrUrl=""):  
        super().__init__()
        self.dbPathOrUrl = dbPathOrUrl

    def getById(self, id: str) -> DataFrame:
        id = str(id)
        if id.isdigit():
            query = """
            PREFIX FOAF: <http://xmlns.com/foaf/0.1>
            PREFIX schema: <http://schema.org/>
            SELECT DISTINCT ?object ?id ?type ?title ?date ?owner ?place ?author ?author_name ?author_id 
            WHERE {
                ?object <http://schema.org/identifier> "%s" .
                ?object <http://schema.org/identifier> ?id .
                ?object <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type .
                ?object <http://schema.org/title> ?title .
                ?object <http://github.com/HelloKittyDataClan/DSexam/owner> ?owner .
                ?object <http://schema.org/itemLocation> ?place .
                 
                OPTIONAL {
                    ?object <http://schema.org/dateCreated> ?date .
                    ?object <http://schema.org/author> ?author .
                    ?author <http://xmlns.com/foaf/0.1/name> ?author_name .
                    ?author <http://schema.org/identifier> ?author_id .
                }
            }
            """ % id
        else:
            query = """
            PREFIX FOAF: <http://xmlns.com/foaf/0.1/>
            PREFIX schema: <http://schema.org/>
            SELECT DISTINCT ?uri ?name ?id 
            WHERE {
                ?uri <http://schema.org/identifier> "%s" ;
                     <http://xmlns.com/foaf/0.1/name> ?name ;
                     <http://schema.org/identifier> ?id .
                ?object <http://schema.org/author> ?uri .
            }
            """ % id
            
        results = get(self.dbPathOrUrl + "sparql", query, True)
        return results




# java -server -Xmx1g -jar blazegraph.jar (terminal command to run Blazegraph)
#Bea

class MetadataQueryHandler(QueryHandler):
    def __init__(self):
        self.dbPathOrUrl = "";
        
    def getAllPeople(self):
        query = """
        PREFIX FOAF: <http://xmlns.com/foaf/0.1/>
        PREFIX schema: <http://schema.org/>

        SELECT DISTINCT ?uri ?author_name ?author_id
        WHERE {
            ?uri a FOAF:Person ;
                 schema:identifier ?author_id ;
                 FOAF:name ?author_name .
        }
        """
        results = get(self.dbPathOrUrl + "sparql",query, True)
        return results

    
    def getAllCulturalHeritageObjects(self):
        query = """
        PREFIX schema: <http://schema.org/>
        PREFIX base_url: <http://github.com/HelloKittyDataClan/DSexam/>
        PREFIX db: <https://dbpedia.org/property/>

        SELECT DISTINCT ?object ?id ?type ?title ?date ?owner ?place ?author ?authorName ?authorID
        WHERE {
            ?object a ?type ;
                    schema:identifier ?id ;
                    schema:title ?title ;
                    base_url:owner ?owner ;
                    schema:itemLocation ?place .
                
            OPTIONAL { ?object schema:dateCreated ?date }
            OPTIONAL {
                ?object schema:author ?author .
                ?author foaf:name ?authorName ;
                schema:identifier ?authorID .
            }
        
            FILTER (?type IN (
                base_url:NauticalChart,
                base_url:ManuscriptPlate,
                base_url:ManuscriptVolume,
                base_url:PrintedVolume,
                base_url:PrintedMaterial,
                db:Herbarium,
                base_url:Specimen,
                db:Painting,
                db:Model,
                db:Map
            ))
        }
        """
        results = get(self.dbPathOrUrl + "sparql", query, True)
        return results       
    

    def getAuthorsOfCulturalHeritageObject(self, object_id: str) -> pd.DataFrame:        #modifica per ottenere un object id con la query giusta
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>

        SELECT DISTINCT ?authorName ?authorID 
        WHERE {{
          ?object schema:identifier "{object_id}" ;
                  schema:author ?uri .

          ?uri schema:identifier ?authorID ;
               foaf:name ?authorName .
        }} 
        """
        results = get(self.dbPathOrUrl + "sparql",query, True)
        return results

    
    def getCulturalHeritageObjectsAuthoredBy(self, personid: str) -> pd.DataFrame:
        query = f"""
        PREFIX schema: <http://schema.org/>
        PREFIX base_url: <http://github.com/HelloKittyDataClan/DSexam/>
        PREFIX db: <https://dbpedia.org/property/>
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>

        SELECT DISTINCT ?object ?id ?type ?title ?date ?owner ?place ?authorName ?authorID
        WHERE {{
            ?object a ?type ;
                    schema:identifier ?id ;
                    schema:title ?title ;
                    base_url:owner ?owner ;
                    schema:itemLocation ?place ;
                    schema:author ?author .

            ?author foaf:name ?authorName ;
                    schema:identifier ?authorID ;
                    schema:identifier "{personid}" .

            OPTIONAL {{ ?object schema:dateCreated ?date }}

            FILTER (?type IN (
                base_url:NauticalChart,
                base_url:ManuscriptPlate,
                base_url:ManuscriptVolume,
                base_url:PrintedVolume,
                base_url:PrintedMaterial,
                db:Herbarium,
                base_url:Specimen,
                db:Painting,
                db:Model,
                db:Map
            ))
        }}
        """
        results = get(self.dbPathOrUrl + "sparql",query, True)
        return results


#_____________QUERIES_____________________________#elena

class ProcessDataQueryHandler(QueryHandler):
    def __init__(self):
        super().__init__()

    def getAllActivities(self):
        try:
            # Modify the partialName parameter to include "wildcard characters" for partial matching
            # nell'input se inserisco anche solo un risultato parziale mi compare comunque
            with connect(self.getDbPathOrUrl()) as con: # metodo ereditato dal query handler, posso connettere al path del relational database graze al getDbPathOrUrl 
                # with / as = construction from panda
               # adds every colums from every table 
                query = """
                    SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                    FROM acquisition
                    UNION 
                    SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", NULL AS objectId, NULL AS technique
                    FROM processing
                    UNION
                    SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", NULL AS objectId, NULL AS technique
                    FROM modelling
                    UNION
                    SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM optimising
                    UNION
                    SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM exporting
                """
                # pd = panda
                # pd.read_sql(query, con) executes the SQL query against the database using the connection con and returns the result as a pandas DataFrame (result of a query)
                result = pd.read_sql(query, con)
                return result
        except Exception as e:
            print(f"An error occurred: {e}")

    def getActivitiesByResponsibleInstitution(self, partialName: str): 
        # questo è un metodo
        #partialName lo da peroni come parametro?, è la stringa di input
        try:
            # Modify the partialName parameter to include "wildcard characters" for partial matching
            # nell'input se inserisco anche solo un risultato parziale mi compare comunque

            partial_name = f"%{partialName}%"
            # allow me to do the partial match
            
            # Connect to the database #modific con la parte di catalina
            with connect(self.getDbPathOrUrl()) as con:
                # Define the SQL query with placeholders for parameters, quindi seleziono tutte le colonne
                # con il FROM indico da che ? .... tabella
                # con il where da che colonna
                query2 = """
                SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                FROM acquisition
                WHERE "responsible institute" LIKE ?
                UNION
                SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                FROM processing
                WHERE "responsible institute" LIKE ?
                UNION
                SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                FROM modelling
                WHERE "responsible institute" LIKE ?
                UNION
                SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                FROM optimising
                WHERE "responsible institute" LIKE ?
                UNION
                SELECT InternalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                FROM exporting
                WHERE "responsible institute" LIKE ?
                """
                # Execute the query with the provided parameters
                # ? = filtration according to the input, non ce l'ho in getallactivities perchè mi riporta tutte le attività
                # qui ce l'ho perchè voglio info solo da un tipo di colonna specifica del db che è responsible institute
                query2_table = pd.read_sql(query2, con, params=[partial_name]*5)
                # The params argument is a list of parameters to be used in the SQL query. Since there are 5 ? placeholders in the query (one for each UNION segment), the list [partial_name]*5 is used to provide the same partial_name parameter for each placeholder.
                return query2_table
            #  The result of the query is returned as a pandas DataFrame and assigned to the variable query2_table.
        except Exception as e:
            print("An error occurred:", e)
            return None

    def getActivitiesByResponsiblePerson(self, partialName: str):
            try:
                partial_name = f"%{partialName}%"
                with connect(self.getDbPathOrUrl()) as con:
                    query3 = """
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                    FROM acquisition
                    WHERE "responsible person" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM processing
                    WHERE "responsible person" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM modelling
                    WHERE "responsible person" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM optimising
                    WHERE "responsible person" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM exporting
                    WHERE "responsible person" LIKE ?
                    """
                    query3_table = pd.read_sql(query3, con, params= [partial_name]*5)
                    return query3_table
            except Exception as e:
                print("An error occurred:", e)
                
    def getActivitiesUsingTool(self, partialName: str):
            try:
                partial_name= f"%{partialName}%"
                with connect(self.getDbPathOrUrl()) as con:
                    query4 = """
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                    FROM acquisition
                    WHERE tool LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM processing
                    WHERE tool LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM modelling
                    WHERE tool LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM optimising
                    WHERE tool LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM exporting
                    WHERE tool LIKE ?
                    """
                    query4_table = pd.read_sql(query4, con, params=[partial_name]*5)
                    return query4_table
            except Exception as e:
                print("An error occurred:", e)
                
    def getActivitiesStartedAfter (self, date: str):
            try:
                date=f"%{date}%"
                with connect(self.getDbPathOrUrl()) as con:
                    query5 = """
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                    FROM acquisition
                    WHERE "start date" LIKE ?
                    UNION
                    -- con l'union faccio 1 +1 con
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM processing
                    WHERE "start date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM modelling
                    WHERE "start date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM optimising
                    WHERE "start date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM exporting
                    WHERE "start date" LIKE ?
                    """
                    query5_table = pd.read_sql(query5, con, params=[date]*5)
                    return query5_table
            except Exception as e:
                print ("An error occured:", e)

    def getActivitiesEndedBefore(self, date: str):
            try:
                date=f"%{date}%"
                with connect (self.getDbPathOrUrl()) as con:
                    query6 = """
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, technique
                    FROM acquisition
                    WHERE "end date" LIKE ?
                    UNION  
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM processing
                    WHERE "end date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM modelling
                    WHERE "end date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM optimising
                    WHERE "end date" LIKE ?
                    UNION
                    SELECT internalId, "responsible institute", "responsible person", tool, "start date", "end date", objectId, NULL AS technique
                    FROM exporting
                    WHERE "end date" LIKE ?
                    """
                    query6_table = pd.read_sql(query6, con, params=[date]*5)
                    return query6_table
            except Exception as e:
                print ("An error occured:", e) 

    def getAcquisitionsByTechnique(self, partialName: str):
        try:
            partial_name = f"%{partialName}%"
            
            with connect(self.getDbPathOrUrl()) as con:
                query = "SELECT * FROM acquisition WHERE technique LIKE ?"
                query_table = pd.read_sql(query, con, params=[partial_name])
                return query_table
        except Exception as e:
            print("An error occurred:", e)
            return None

process_query = ProcessDataQueryHandler()
process_query.setDbPathOrUrl("activities.db")
